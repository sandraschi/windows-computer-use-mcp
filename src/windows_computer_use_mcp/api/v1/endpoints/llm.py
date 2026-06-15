"""Local LLM bridge: OpenAI-compatible API (Ollama, LM Studio) for the web_sota chat UI."""

from __future__ import annotations

import logging
import os
from typing import Any, Literal
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from windows_computer_use_mcp.llm_repo_context import REPO_CONTEXT_MARKDOWN

logger = logging.getLogger(__name__)

router = APIRouter(tags=["llm"])

DEFAULT_BASE = os.getenv("PYWINAUTO_LLM_BASE_URL", "http://127.0.0.1:11434/v1").rstrip("/")

REFINER_SYSTEM = """You are a prompt-refinement assistant for operators using pywinauto-mcp (Windows desktop automation).
Rewrite the user's message to be clearer, more specific, and easier for a coding/automation assistant to act on.
Output only the refined prompt text — no quotes, no preamble, no markdown fences."""


def _allowed_llm_base(url: str) -> bool:
    try:
        p = urlparse(url)
        if p.scheme not in ("http", "https"):
            return False
        h = (p.hostname or "").lower()
        return h in ("127.0.0.1", "localhost", "::1")
    except Exception:
        return False


def _resolve_base(base_url: str | None) -> str:
    raw = (base_url or DEFAULT_BASE).strip().rstrip("/")
    if not _allowed_llm_base(raw):
        raise HTTPException(
            status_code=400,
            detail="base_url must be http(s)://127.0.0.1, localhost, or ::1 (SSRF protection)",
        )
    return raw


class ChatMessage(BaseModel):
    """OpenAI-style chat message."""

    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    """Non-streaming chat completion request."""

    model: str = Field(..., description="Model id as reported by /v1/models")
    messages: list[ChatMessage]
    base_url: str | None = Field(None, description="OpenAI-compatible root, e.g. http://127.0.0.1:11434/v1")
    temperature: float | None = Field(0.7, ge=0, le=2)


class ChatResponse(BaseModel):
    """Assistant text or error string from the upstream LLM."""

    content: str | None = None
    model: str | None = None
    raw_error: str | None = None


class RefineRequest(BaseModel):
    """Single-shot prompt refinement request."""

    draft: str
    model: str
    base_url: str | None = None


@router.get("/config")
async def llm_config() -> dict[str, Any]:
    """Defaults for the web UI (Ollama vs LM Studio presets)."""
    return {
        "default_base_url": DEFAULT_BASE,
        "presets": [
            {"id": "ollama", "label": "Ollama", "base_url": "http://127.0.0.1:11434/v1"},
            {"id": "lmstudio", "label": "LM Studio", "base_url": "http://127.0.0.1:1234/v1"},
        ],
    }


@router.get("/repo-context")
async def repo_context() -> dict[str, str]:
    """Markdown block to inject as repository knowledge in system prompts."""
    return {"markdown": REPO_CONTEXT_MARKDOWN}


@router.get("/models")
async def list_models(
    base_url: str | None = Query(None, description="OpenAI-compatible API root"),
) -> dict[str, Any]:
    """Proxy GET /v1/models to the local LLM server."""
    base = _resolve_base(base_url)
    url = f"{base}/models"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(url)
    except httpx.RequestError as e:
        logger.warning("LLM models fetch failed: %s", e)
        raise HTTPException(status_code=502, detail=f"Could not reach LLM at {base}: {e}") from e

    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text[:2000])

    try:
        data = r.json()
    except Exception:
        raise HTTPException(status_code=502, detail="Invalid JSON from LLM /models") from None
    return data


@router.post("/chat", response_model=ChatResponse)
async def chat_completions(body: ChatRequest) -> ChatResponse:
    """Proxy POST /v1/chat/completions (non-streaming)."""
    base = _resolve_base(body.base_url)
    url = f"{base}/chat/completions"
    payload: dict[str, Any] = {
        "model": body.model,
        "messages": [m.model_dump() for m in body.messages],
        "stream": False,
    }
    if body.temperature is not None:
        payload["temperature"] = body.temperature

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            r = await client.post(url, json=payload)
    except httpx.RequestError as e:
        logger.warning("LLM chat failed: %s", e)
        return ChatResponse(content=None, raw_error=str(e))

    if r.status_code >= 400:
        return ChatResponse(content=None, raw_error=r.text[:4000])

    try:
        data = r.json()
    except Exception as e:
        return ChatResponse(content=None, raw_error=f"Invalid JSON: {e}")

    try:
        choice = data["choices"][0]
        msg = choice.get("message") or {}
        text = msg.get("content")
        return ChatResponse(content=text, model=data.get("model"))
    except (KeyError, IndexError, TypeError) as e:
        return ChatResponse(content=None, raw_error=f"Unexpected response shape: {e!s} — {data!s}"[:4000])


@router.post("/refine", response_model=ChatResponse)
async def refine_prompt(body: RefineRequest) -> ChatResponse:
    """One-shot prompt refinement using the same chat endpoint."""
    if not body.draft.strip():
        raise HTTPException(status_code=400, detail="draft is empty")

    req = ChatRequest(
        model=body.model,
        base_url=body.base_url,
        messages=[
            ChatMessage(role="system", content=REFINER_SYSTEM),
            ChatMessage(role="user", content=body.draft),
        ],
        temperature=0.3,
    )
    return await chat_completions(req)

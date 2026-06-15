"""LLM provider discovery endpoint."""

from __future__ import annotations

import httpx
from fastapi import APIRouter

router = APIRouter(prefix="/api/llm", tags=["llm"])


@router.get("/providers")
async def get_llm_providers():
    providers = []
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get("http://127.0.0.1:11434/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                models = [m["name"] for m in data.get("models", [])]
                providers.append(
                    {
                        "id": "ollama",
                        "label": "Ollama",
                        "base_url": "http://127.0.0.1:11434/v1",
                        "models": models,
                        "needs_key": False,
                    }
                )
    except Exception:
        providers.append(
            {
                "id": "ollama",
                "label": "Ollama",
                "base_url": "http://127.0.0.1:11434/v1",
                "models": [],
                "needs_key": False,
            }
        )
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get("http://127.0.0.1:1234/v1/models")
            if resp.status_code == 200:
                data = resp.json()
                models = [m["id"] for m in data.get("data", [])]
                providers.append(
                    {
                        "id": "lmstudio",
                        "label": "LM Studio",
                        "base_url": "http://127.0.0.1:1234/v1",
                        "models": models,
                        "needs_key": False,
                    }
                )
    except Exception:
        providers.append(
            {
                "id": "lmstudio",
                "label": "LM Studio",
                "base_url": "http://127.0.0.1:1234/v1",
                "models": [],
                "needs_key": False,
            }
        )
    return {"providers": providers}

# LLM repository context (web chat)

The **canonical** text injected into the local-LLM system prompt lives in:

- `src/windows_computer_use_mcp/llm_repo_context.py` → `REPO_CONTEXT_MARKDOWN`

The dev UI loads it via **`GET /api/v1/llm/repo-context`**. Edit the Python module when tools or safety behavior change, then rebuild/restart the backend.

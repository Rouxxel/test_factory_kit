# Project Learnings & Gotchas

> **Rule:** Keep this file concise (under 30 bullet points). Only add reusable, non-obvious technical gotchas discovered during execution (e.g., build quirks, test environment rules, library pitfalls). Every subagent must read this before starting work.

## Environment & Tooling
- Backend runs from `backend/` as cwd: `from app...` imports and the `.env` path in `config.py` are relative to it. Run `pytest backend/tests` from repo root (pytest adds `backend/` to sys.path).
## Codebase & Architecture Gotchas
- `GeminiService.stream_chat` catches only `APIError`, `httpx.HTTPError` and `ValueError` and emits an error event without `[DONE]`. Other exception types propagate.
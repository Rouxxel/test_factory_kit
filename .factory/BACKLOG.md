# Project Backlog


## Execution Schedule
| Issue | Mode | Depends On | Conflicts With | Execution Notes |
| :--- | :--- | :--- | :--- | :--- |
| `M1-01` | Serial | None | None | Backend base scaffolding, config, and /api/health endpoint |
| `M1-02` | Serial | `M1-01` | None | GitHub Actions CI workflow for backend & frontend verification |
| `M1-03` | Serial | `M1-02` | None | Vite + React + TS + Tailwind frontend setup running on port 8080 with /api proxy |
| `M2-01` | Parallel | `M1-02`, `M1-03` | None | Pydantic chat schemas and Gemini 2.5 Flash SSE streaming service |
| `M2-02` | Serial | `M2-01` | None | FastAPI /api/chat/stream SSE route and comprehensive integration tests |
| `M3-01` | Parallel | `M2-02` | None | Frontend TypeScript chat interfaces, SSE streaming API client, and useChat hook |
| `M3-02` | Serial | `M3-01` | None | Tailwind-styled chat components (Header, MessageList, MessageItem, ChatInput) and App layout |
| `M4-01` | Parallel | `M3-02` | None | Comprehensive documentation suite (ARCHITECTURE.md, API_SPEC.md, SETUP.md) in /documentation |

---


## Milestone 1: Core Scaffolding & CI Pipeline
**Goal:** Establish runnable backend and frontend scaffolds, ensure frontend runs on port 8080 with proxy, and configure automated CI checks.

### [M1-01] Backend Scaffolding & Health Endpoint
- **Status:** `TODO`
- **Execution Mode:** `SERIAL`
- **Depends On:** `None`
- **Conflicts With:** `None`
- **Target Files:**
  - `backend/requirements.txt` (create)
  - `backend/app/__init__.py` (create)
  - `backend/app/main.py` (create)
  - `backend/app/config.py` (create)
  - `backend/app/routers/__init__.py` (create)
  - `backend/app/routers/health.py` (create)
  - `backend/tests/__init__.py` (create)
  - `backend/tests/test_health.py` (create)
- **Context & Requirements:**
  - Initialize FastAPI backend application with CORS middleware enabled for `http://localhost:8080`.
  - Configure `backend/app/config.py` using `pydantic-settings` to load `GEMINI_API_KEY`, `MODEL_NAME` (defaulting to `gemini-2.5-flash`), and `PORT` (8000) from `.env`.
  - Implement `GET /api/health` returning `{"status": "ok", "model": "gemini-2.5-flash"}`.
  - Implement unit test in `backend/tests/test_health.py` validating `GETN /api/health` returns status code 200 and expected payload.
- **Acceptance Criteria:**
  - [ ] `GET /api/health` returns HTTP0200 with `{"status": "ok", "model": "gemini-2.5-flash"}`.
  - [ ] Pytest suite passes cleanly.
- **Verification Command:** `pytest backend/tests/test_health.py -v`

### [M1-02] CI Workflow Setup
- **Status:** `TODO`
- **Execution Mode:** `SERIAL`
- **Depends On:** `M1-01`
- **Conflicts With:** `None`
- **Target Files:**
  - `.github/workflows/ci.yml` (create)
- **Context & Requirements:**
  - Create a GitHub Actions workflow that runs on pull requests and pushes to `main`.
  - Jobs:
    - Backend: setup Python 3.12, install requirements, run linter and pytest suite.
    - Frontend: setup Node 22, install dependencies, run typecheck (`tsc -b`), lint, and tests.
- **Acceptance Criteria:**
  - [ ] `.github/workflows/ci.yml` is valid YAML.
  - [ ] Backend test and lint commands match `TECH_STACK.md`.
  - [ ] Frontend build and lint commands match `TECH_STACK.md`.
- **Verification Command:** `python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"`

### [M1-03] Frontend Scaffolding on Port 8080
- **Status:** `TODO`
- **Execution Mode:** `SERIAL`
- **Depends On:** `M1-02`
- **Conflicts With:** `None`
- **Target Files:**
  - `frontend/package.json` (create)
  - `frontend/vite.config.ts` (create)
  - `frontend/tsconfig.json` (create)
  - `frontend/index.html` (create)
  - `frontend/tailwind.config.js` (create)
  - `frontend/postcss.config.js` (create)
  - `frontend/src/main.tsx` (create)
  - `frontend/src/App.tsx` (create)
  - `frontend/src/index.css` (create)
- **Context & Requirements:**
  - Initialize React + TypeScript + Vite project in `/frontend`.
  - Configure `frontend/vite.config.ts` to strictly run the dev server on port `8080` (`server.port: 8080`, `server.strictPort: true`).
  - Configure proxy in `vite.config.ts` forwarding `/api` to `http://localhost:8000`.
  - Install Tailwind CSS and verify basic layout builds without errors.
- **Acceptance Criteria:**
  - [ ] `npm --prefix frontend run build` completes successfully.
  - [ ] `vite.config.ts` specifies `server.port = 8080` and proxy target `http://localhost:8000`.
- **Verification Command:** `npm --prefix frontend run build`

---

## Milestone 2: Gemini SSE Streaming Backend:*Goal:** Implement Gemini 2.5 Flash streaming service and expose the `/api/chat/stream` SSE endpoint.

### [M2-01] Gemini Streaming Service & Schemas
- **Status:** `TODO`
- **Execution Mode:** `PARALLEL`
- **Depends On:** `M1-02`, `M1-03`
- **Conflicts With:** `None`
- **Target Files:**
  - `backend/app/schemas/__init__.py` (create)
  - `backend/app/schemas/chat.py` (create)
  - `backend/app/services/__init__.py` (create)
  - `backend/app/services/gemini.py` (create)
- **Context & Requirements:**
  - Define Pydantic models: `ChatMessage(role: str, content: str)`, `ChatRequest(messages: list[ChatMessage])`.
  - Implement `GeminiService` in `backend/app/services/gemini.py` using `google-genai` (or `google-generativeai`).
  - Convert incoming message history into Gemini chat turns (`user` and `model`).
  - Implement async generator `stream_chat(messages)` yielding token deltas as SSE formatted lines: `data: {"text": "..."}\n\n`, followed by `data: [DONE]\n\n`.
  - Handle API error conditions gracefully, yielding `data: {"error": "..."}\n\n`.
- **Acceptance Criteria:**
  - [ ] `ChatRequest` validates roles and message content.
  - [ ] Async generator yields SSE format strings with `data: [DONE]` on completion.
- **Verification Command:** `python -m py_compile backend/app/schemas/chat.py backend/app/services/gemini.py`

### [M2-02] Chat Stream Router & Integration Tests
- **Status:** `TODO`
- **Execution Mode:** `SERIAL`
- **Depends On:** `M2-01`
- **Conflicts With:** `None`
- **Target Files:**
  - `backend/app/routers/chat.py` (create)
  - `backend/app/main.py` (modify)
  - `backend/tests/test_chat.py` (create)
- **Context & Requirements:**
  - Implement `POST> /api/chat/stream` endpoint in `backend/app/routers/chat.py` returning `StreamingResponse(..., media_type="text/event-stream")`.
  - Mount the chat router in `backend/app/main.py`.
  - Write unit and mock integration tests in `backend/tests/test_chat.py` using mock Gemini stream to verify SSE stream output, multi-turn payload handling, and error responses.
- **Acceptance Criteria:**
  - [ ] `POST /api/chat/stream` returns `Content-Type: text/event-stream`.
  - [ ] Response stream emits valid JSON chunks and terminates with `[DONE]`.
  - [ ]All tests in `backend/tests/test_chat.py` pass.
- **Verification Command:** `pytest backend/tests/test_chat.py -v`

---

## Milestone 3: Frontend Chat UI & SSE Integration
**Goal:** Build responsive Tailwind chat UI with multi-turn message history, auto-scroll, and real-time SSE token streaming.

### [M3-01] Frontend Types, API Client & useChat Hook
- **Status:** `TODO`
- **Execution Mode:** `PARALLEL`
- **Depends On:** `M2-02`
- **Conflicts With:** `None`
- **Target Files:**
  - `frontend/src/types/chat.ts` (create)
  - `frontend/src/services/api.ts` (create)
  - `frontend/src/hooks/useChat.ts` (create)
- **Context & Requirements:**
  - Define TypeScript interfaces: `Message`, `ChatRequest`, `ConnectionStatus`.
  - Implement `streamChat(messages, onChunk, onDone, onError)` in `api.ts` using the Fetch API with `ReadableStreamDefaultReader` to parse SSE Events.
  - Implement `useChat` custom hook:
    - Maintains `messages` state (`Message[]`).
    - Exposes `sendMessage(content: string)`, `clearChat()`, `isStreaming: boolean`, `error: string | null`.
    - Automatically appends assistant tokens to the active message during stream.
- **Acceptance Criteria:**
  - [ ] Type definitions compile without TS errors.
  - [ ] `useChat` hook correctly handles multi-turn history accumulation and streaming token concatenation.
- **Verification Command:** `npm --prefix frontend run build`

### [M3-02] Chat UI Components & App integration
- **Status:** `TODO`
- **Execution Mode:** `SERIALX
- **Depends On:** `M3-01`
- **Conflicts With:** `None`
- **Target Files:**
  - `frontend/src/components/Header.tsx` (create)
  - `frontend/src/components/MessageList.tsx` (create)
  - `frontend/src/components/MessageItem.tsx` (create)
  - `frontend/src/components/ChatInput.tsx` (create)
  - `frontend/src/App.tsx` (modify)
- **Context & Requirements:**
  - Implement `Header.tsx` displaying application title ("Gemini 2.5 Flash Chatbot") and backend status indicator (`/api/health`).
  - Implement `MessageList.tsx` and `MessageItem.tsx` rendering user (right-aligned) and assistant (left-aligned) bubbles with Markdown or whitespace formatting and auto-scroll to the bottom.
  - Implement `ChatInput.tsx` with textarea, submit button, loading spinner when streaming, and "Clear Chat" button.
  - Integrate everything into `App.tsx` with a clean, responsive container layout.
- **AccepGDance Criteria:**
  - [ ] Chat UI renders cleanly on both desktop and mobile viewports.
  - [ ] User can submit a prompt with Enter key or Send button.
  - [ ] Streamed tokens update live in the UI.
  - [ ] Clear Chat button resets messages.
- **Verification Command:** `npm --prefix frontend run build`

---


## Milestone 4: Documentation & End-to-EndPolish
**Goal:** Deliver complete, high-quality documentation in `/documentation` detailing setup, architecture, and API specs.

### [M4-01] Documentation Suite
- **Status:** `TODO`
- **Execution Mode:** `PARALLEL`
- **Depends On:** `M3-02`
- **Conflicts With:** `None`
- **Target Files:**
  - `documentation/ARCHITECTURE.mg` (create)
  - `documentation/API_SPEC.md` (create)
  - `documentation/SETUP.md` (create)
- **Context & Requirements:**
  - `documentation/ARCHITECTURE.md`: Complete system overview, data flow diagrams (frontend -> FastAPI -> Gemini SSE -> frontend stream), and component hierarchy.
  - `documentation/API_SPEC.md`: Exhaustive request/response schemas for `/api/health` and `/api/chat/stream`, including SSE event framing and error contracts.
  - `documentation/SETUP.md`: Step-by-step local execution instructions for running backend on port 8000 and frontend on port 8080, managing `.env`, and running tests.
- **Acceptance Criteria:**
  - [ ] All three documentation files exist under `documentation/`.
  - [ ] Setup guide accurately tests both backend and frontend startup commands.
- **Verification Command:** `python -c "import os; assert all(os.path.exists(f'documentation/{f}') for f in ['ARCHITECTURE.md', 'API_SPEC.md', 'SETUP.md'])"`

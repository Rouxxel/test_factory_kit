# System Architecture

## 1. Directory & File Map
```text
test_factory_kit/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI app initialization, CORS, router inclusion
│   │   ├── config.py           # Pydantic settings loading from .env (API key, model)
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── chat.py         # Message & ChatRequest Pydantic schemas (with timestamp & sender)
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── gemini.py       # Gemini API client wrapper & SSE streaming generator
│   │   └── routers/
│   │       ├── __init__.py
│   │       ├── health.py       # GET /api/health
│   │       └── chat.py         # POST /api/chat/stream (SSE)
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_health.py
│   │   └── test_chat.py
│   ├── requirements.txt
│   ├── .env.example
│   └── .env                    # Local untracked key storage
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Header.tsx      # App title and connection badge
│   │   │   ├── MessageList.tsx # Chat bubbles container with auto-scroll
│   │   │   ├── MessageItem.tsx # Message bubble with sender label, timestamp, and content
│   │   │   └── ChatInput.tsx   # Textarea/input, Send button, Clear button
│   │   ├── hooks/
│   │   │   └── useChat.ts      # Multi-turn state (with timestamps), SSE reader, error states
│   │   ├── services/
│   │   │   └── api.ts          # Fetch wrappers for health check and SSE streaming
│   │   ├── types/
│   │   │   └── chat.ts         # TypeScript interfaces (Message, ChatRequest, StreamChunk)
│   │   ├── App.tsx             # Root layout & view composition
│   │   ├── main.tsx            # React entrypoint
│   │   └── index.css           # Tailwind base directives
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts          # Port 8080 and /api proxy configuration
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   └── postcss.config.js
└── documentation/
    ├── ARCHITECTURE.md         # Full system architecture and flow diagrams
    ├── API_SPEC.md             # REST and SSE API contract reference
    └── SETUP.md                # Local environment setup and execution guide
```

## 2. Module Boundaries & Responsibilities
- **Backend Service Layer (`backend/app/services/gemini.py`):** Wraps the Google GenAI SDK. Transforms chat history into Gemini prompt contents and yields token chunks asynchronously.
- **Backend API Layer (`backend/app/routers/`):** Exposes `/api/health` and `/api/chat/stream`. Emits standard Server-Sent Events (`text/event-stream`).
- **Frontend Hook Layer (`frontend/src/hooks/useChat.ts`):** Encapsulates message history with `id`, `role`, `content`, and `timestamp`, active streaming accumulator, abort controller, and error handling.
- **Frontend Presentation Layer (`frontend/src/components/`):** Tailwind-styled UI components, responsive layout, message bubbles displaying sender name badge, timestamp, and message body.

## 3. Data Models & API Contracts
- **Message Schema:**
  ```json
  {
    "role": "user" | "assistant",
    "content": "string",
    "timestamp": "string"
  }
  ```
- **Chat Request (`POST /api/chat/stream`):**
  ```json
  {
    "messages": [
      { "role": "user", "content": "Hello", "timestamp": "2026-11-26T12:00:00Z" },
      { "role": "assistant", "content": "Hi there! How can I help?", "timestamp": "2026-11-26T12:00:02Z" }
    ]
  }
  ```
- **SSE Stream Protocol:**
  - Content-Type: `text/event-stream`
  - Delta chunk: `data: {"text": "chunk text"}\n\n`
  - Stream completion: `data: [DONE]\n\n`
  - Error event: `data: {"error": "Error message"}\n\n`
- **Health Check (`GET /api/health`):**
  - Response: `{"status": "ok", "model": "gemini-2.5-flash"}`

## 4. Shared / High-Contention Files
- `frontend/src/types/chat.ts` (API contracts used across frontend hooks and components)
- `backend/app/schemas/chat.py` (Pydantic schemas used across routers and services)
- `frontend/vite.config.ts` (Proxy rules and port settings)

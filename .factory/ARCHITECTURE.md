# System Architecture

## 1. Directory & File Map
\\\	ext
test_factory_kit/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI app initialization, CORS, router inclusion
│   │   ├── config.py           # Pydantic settings loading from .env (API key, model)
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── chat.py         # Message & ChatRequest Pydantic schemas
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
│   │   │   ├── MessageItem.tsx # Individual user/assistant message bubble
│   │   │   └── ChatInput.tsx   # Textarea/input, Send button, Clear button
│   │   ├── hooks/
│   │   │   └── useChat.ts      # Multi-turn state, SSE reader, error states
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
\\\

## 2. Module Boundaries & Responsibilities
- **Backend Service Layer (ackend/app/services/gemini.py):** Wraps the Google GenAI SDK. Transforms chat history into Gemini prompt contents and yields token chunks asynchronously.
- **Backend API Layer (ackend/app/routers/):** Exposes /api/health and /api/chat/stream. Emits standard Server-Sent Events (	ext/event-stream).
- **Frontend Hook Layer (rontend/src/hooks/useChat.ts):** Encapsulates message history, active streaming accumulator, abort controller, and error handling.
- **Frontend Presentation Layer (rontend/src/components/):** Tailwind-styled UI components, responsive layout, auto-scrolling message view.

## 3. Data Models & API Contracts
- **Message Schema:**
  \\\json
  {
    "role": "user" | "assistant",
    "content": "string"
  }
  \\\
- **Chat Request (POST /api/chat/stream):**
  \\\json
  {
    "messages": [
      { "role": "user", "content": "Hello" },
      { "role": "assistant", "content": "Hi there! How can I help?" },
      { "role": "user", "content": "What was my first message?" }
    ]
  }
  \\\
- **SSE Stream Protocol:**
  - Content-Type: 	ext/event-stream
  - Delta chunk: data: {"text": "chunk text"}\n\n
  - Stream completion: data: [DONE]\n\n
  - Error event: data: {"error": "Error message"}\n\n
- **Health Check (GET /api/health):**
  - Response: {"status": "ok", "model": "gemini-2.5-flash"}

## 4. Shared / High-Contention Files
- rontend/src/types/chat.ts (API contracts used across frontend hooks and components)
- ackend/app/schemas/chat.py (Pydantic schemas used across routers and services)
- rontend/vite.config.ts (Proxy rules and port settings)

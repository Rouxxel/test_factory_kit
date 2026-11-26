# Product Requirements Document (PRD)

## 1. Problem & Goal
A lightweight, modern web-based chatbot application that allows users to interact with Google's Gemini 2.5 Flash model in real-time. The application runs entirely on localhost and demonstrates the spec-driven factory-loop development process with clean separation between a FastAPI backend and a React + TypeScript + Vite + Tailwind frontend.

## 2. Core User Flows & Features
- **Real-Time Streaming Chat:** User types a message and submits it; the assistant streams back text tokens incrementally using Server-Sent Events (SSE).
- **Multi-Turn Context:** The user can conduct ongoing, back-and-forth conversations where the model remembers prior turns within the active session.
- **Session Reset:** A "Clear Chat" button allows the user to reset conversation history and start fresh.
- **Status & Health Monitoring:** A visual connection status indicator based on the backend /api/health endpoint.
- **Port & Network Layout:**
  - Frontend runs on http://localhost:8080.
  - Backend runs on http://localhost:8000.
  - Vite dev server proxies /api requests to backend to avoid CORS complications.
- **Documentation:** A dedicated /documentation folder containing architecture reference, API specifications, and setup instructions.

## 3. Explicit Non-Goals (Out of Scope)
- Persistent database storage (conversations are held in-memory in client state).
- User authentication, login, or multi-tenant user accounts.
- File uploads, document processing, voice/audio input, or image generation.
- Production cloud deployment (strictly targeted for localhost development).

## 4. Global Success Criteria
- User can send a message and see real-time streaming tokens from Gemini 2.5 Flash.
- Multi-turn conversation retains previous context accurately.
- Frontend launches on port 8080 without port collisions.
- 100% automated test coverage for backend endpoints and core frontend components.
- Complete documentation available in /documentation/.

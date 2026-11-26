# Tech Stack & Verification Commands

## 1. Stack & Key Dependencies
- **Language / Runtime:**
  - Backend: Python 3.12
  - Frontend: TypeScript 5.x / Node.js 22.x
- **Backend Framework & Libraries:**
  - astapi (API framework)
  - uvicorn[standard] (ASGI server)
  - google-genai (Official Gemini SDK)
  - pydantic & pydantic-settings (Data validation and config)
  - python-dotenv (Local environment variable loading)
  - pytest, pytest-asyncio, httpx (Testing suite)
- **Frontend Framework & Libraries:**
  - eact & eact-dom (v18 or v19)
  - ite (Build tool and dev server)
  - 	ailwindcss, postcss, utoprefixer (Styling)
  - lucide-react (Icons)
  - itest, @testing-library/react (Frontend testing)

## 2. Canonical CLI Commands
- **Install:**
  - Backend: pip install -r backend/requirements.txt
  - Frontend: 
pm --prefix frontend install
- **Build / Typecheck:**
  - Backend: python -m py_compile backend/app/main.py
  - Frontend: 
pm --prefix frontend run build
- **Lint / Format:**
  - Backend: python -m flake8 backend (or python -m ruff check backend)
  - Frontend: 
pm --prefix frontend run lint
- **Test (Single File/Slice):**
  - Backend: pytest backend/tests/test_health.py -v
  - Frontend: 
pm --prefix frontend test -- src/components/ChatInput.test.tsx
- **Test (Full Suite):**
  - Backend: pytest backend/tests -v
  - Frontend: 
pm --prefix frontend test --run
"@ | Out-File -FilePath .factory/TECH_STACK.md -Encoding utf8;

@"
# Configured MCP Servers & Usage Rules

## Active MCPs
- **factory-session-hub:**
  - **When to use:** Orchestrator session dispatch (actory_session_dispatch), subagent worker reporting (actory_worker_report), progress tracking (actory_worker_progress), incident logging (actory_report_incident), and review gate feedback (actory_session_send_feedback).
  - **Rules:** Never edit files inside .factory/sessions/ directly; coordinate exclusively via MCP tools.

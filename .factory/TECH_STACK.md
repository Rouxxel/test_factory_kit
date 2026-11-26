# Tech Stack & Verification Commands

## 1. Stack & Key Dependencies
- **Language / Runtime:**
  - Backend: Python 3.12
  - Frontend: TypeScript 5.x / Node.js 22.x
- **Backend Framework & Libraries:**
  - fastapi (API framework)
  - uvicorn[standard] (ASGI server)
  - google-genai (Official Gemini SDK)
  - pydantic & pydantic-settings (Data validation and config)
  - python-dotenv (Local environment variable loading)
  - pytest, pytest-asyncio, httpx (Testing suite)
  - ruff (Linter)
- **Frontend Framework & Libraries:**
  - react & react-dom (v18 or v19)
  - vite (Build tool and dev server)
  - tailwindcss, postcss, autoprefixer (Styling)
  - lucide-react (Icons)
  - vitest, @testing-library/react (Frontend testing)
  - eslint (Linter)

## 2. Canonical CLI Commands
- **Install:**
  - Backend: `pip install -r backend/requirements.txt`
  - Frontend: `npm --prefix frontend install`
- **Build / Typecheck:**
  - Backend: `python -m py_compile backend/app/main.py`
  - Frontend: `npm --prefix frontend run build`
- **Lint / Format:**
  - Backend: `python -m ruff check backend`
  - Frontend: `npm --prefix frontend run lint`
- **Test (Single File/Slice):**
  - Backend: `pytest backend/tests/test_health.py -v`
  - Frontend: `npm --prefix frontend test -- src/components/ChatInput.test.tsx`
- **Test (Full Suite):**
  - Backend: `pytest backend/tests -v`
  - Frontend: `npm --prefix frontend test -- --run`
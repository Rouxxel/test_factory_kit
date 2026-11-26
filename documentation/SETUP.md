# Local Setup Guide

Run the backend on port 8000 and the frontend on port 8080. The frontend dev server proxies `/api/*` to the backend, so open the app at <http://localhost:8080>.

## Prerequisites

- Python 3.12
- Node.js 22.x and npm
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)

Run all commands from the repository root unless a step says otherwise.

## 1. Backend (port 8000)

### 1.1 Create a virtual environment and install dependencies

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

If PowerShell blocks the activation script, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, or call `.\.venv\Scripts\python.exe -m ...` directly.

bash / zsh (macOS, Linux, Git Bash):

```bash
python3 -m venv .venv
source .venv/bin/activate        # Git Bash on Windows: source .venv/Scripts/activate
pip install -r backend/requirements.txt
```

### 1.2 Configure the API key

Windows PowerShell:

```powershell
Copy-Item backend/.env.example backend/.env
```

bash:

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` and replace the placeholder:

```text
GEMINI_API_KEY=<your key>
MODEL_NAME=gemini-2.5-flash
PORT=8000
```

`backend/.env` is git-ignored. Never commit it or paste a real key into any tracked file. Without a key, `/api/health` still works, but chat requests return the `error` SSE event.

### 1.3 Start the server

The server must start from `backend/`. The `app` package is imported relative to that directory, and `.env` is read from the current working directory.

Windows PowerShell:

```powershell
cd backend
uvicorn app.main:app --port 8000
```

bash:

```bash
cd backend && uvicorn app.main:app --port 8000
```

Add `--reload` for auto-restart while developing. Stop the server with Ctrl+C.

### 1.4 Check it

```bash
curl http://localhost:8000/api/health
# {"status":"ok","model":"gemini-2.5-flash"}
```

Interactive docs are at <http://localhost:8000/docs>.

## 2. Frontend (port 8080)

In a second terminal, from the repository root:

```bash
npm --prefix frontend install
npm --prefix frontend run dev
```

Vite listens on <http://localhost:8080> with `strictPort`, so it fails instead of picking another port if 8080 is taken. The Vite proxy forwards `/api` to `http://localhost:8000`, so the backend must be running for the header badge to show "Connected".

## 3. Tests, lint and build

Run from the repository root with the virtual environment active for the backend commands.

| Check | Backend | Frontend |
| --- | --- | --- |
| Build / typecheck | `python -m py_compile backend/app/main.py` | `npm --prefix frontend run build` |
| Lint | `python -m ruff check backend` | `npm --prefix frontend run lint` |
| Tests | `pytest backend/tests -v` | `npm --prefix frontend test -- --run` |
| Single test file | `pytest backend/tests/test_health.py -v` | `npm --prefix frontend test -- src/components/ChatInput.test.tsx` |

The backend tests mock Gemini, so they need no API key or network. The same commands run in CI (`.github/workflows/ci.yml`).

## Troubleshooting

- **`ModuleNotFoundError: No module named 'app'`:** you started uvicorn from the repository root. Run `cd backend` first.
- **Header shows "Disconnected":** the backend is not running on port 8000, or the frontend was not started with `npm run dev` (the proxy exists only in the dev server).
- **Chat replies with an error message:** `GEMINI_API_KEY` is missing or invalid, or the Gemini API call failed. The server log shows the exception class name.
- **Port already in use:** stop the other process. The frontend will not fall back to another port, and the CORS rule and proxy assume 8080 and 8000.
- **`pytest` or `ruff` not found:** activate the virtual environment (step 1.1).

LeetCode Solution Assistant – Backend
====================================

FastAPI + LangGraph backend that powers the LeetCode Solution Assistant. It classifies each chat turn (question explanation, code request, corrections, etc.), routes through tailored prompts, and returns the assistant reply while keeping per-user session state in memory.

Features
--------
- FastAPI app with CORS enabled for localhost and the browser extension.
- Session management via `fastapi-sessions` (cookie, header, or query `session_id`).
- LangGraph pipeline that classifies intents and runs focused nodes for explanations, solution walkthroughs, code fixes, or language clarification.
- Simple in-memory backend storage (UUID keyed) for quick local runs.
- Lightweight tests that stub the LLM to validate routing.

Project layout
--------------
- `main.py` – FastAPI routes and session wiring.
- `chat_service.py` – Bridges HTTP requests to the LangGraph and returns replies.
- `ai.py` – Builds the LangGraph (intent classifier + handler nodes).
- `models.py` / `state.py` / `state_adapter.py` – Data models and conversions between stored session data and LangChain messages.
- `session_setup.py` – Cookie + verifier setup and session resolution helpers.
- `test.py` – Offline tests with a stubbed LLM.

Requirements
------------
- Python 3.11+
- Anthropic API key (set `ANTHROPIC_API_KEY` in your environment)
- (Optional) `.env` file is loaded automatically via `python-dotenv`.

Setup
-----
1) Create and activate a virtualenv in the repo root:
```
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```
2) Install dependencies (PEP 621 list is in `pyproject.toml`):
```
pip install anthropic fastapi-sessions "fastapi[standard]" httpx "langchain[anthropic]" langgraph pytest python-dotenv trio "uvicorn[standard]"
```
3) Add your API key to `.env` or your shell:
```
export ANTHROPIC_API_KEY=sk-...
```

Running the API
---------------
From the repo root:
```
uvicorn backend.main:app --reload --port 8000
```
By default the service accepts CORS requests from `http://localhost`, `http://localhost:8000`, `http://127.0.0.1:8000`, and `chrome-extension://*`.

API quick reference
-------------------
- `POST /create_session/{name}` – Creates a session, sets a cookie, and returns `session_id`.
- `GET /whoami` – Returns stored session data for the current session.
- `POST /questions` – Body: `{"lc_question_number": <int>}`. Sends a “store this LeetCode question” message to the graph; reply should be “Got it!”.
- `POST /chat` – Body: `{"text": "<user message>"}`. Runs the message through the classifier + node graph and returns the assistant reply and message type.
- `POST /delete_session` – Deletes the current session and clears the cookie.

Session propagation
-------------------
The backend accepts a session id via:
- Cookie set by `/create_session/{name}`
- Header `X-Session-ID`
- Query param `session_id`

LangGraph flow (high level)
---------------------------
1) Planner node classifies the latest user message into one of the defined types (question explanation, solution explanation, code request/correction, etc.).
2) Router node jumps to the matching handler node.
3) Handler nodes apply targeted system prompts and return an AI message.
4) State is converted back to stored messages and persisted to the in-memory session backend.

Testing
-------
Run tests from the `backend` directory:
```
pytest
```
Tests stub the LLM, so they do not call external services.

Notes
-----
- The in-memory session backend is for local development only; swap it out for a persistent store for production.
- Keep your API key out of source control; rely on environment variables or `.env` locally.

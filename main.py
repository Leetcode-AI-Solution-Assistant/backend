from __future__ import annotations

from uuid import uuid4

from fastapi import Depends, FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware

from models import ChatIn, QuestionIn, SessionData
from session_setup import (SessionContext, backend, cookie, get_session_context,)
from chat_service import apply_user_message_and_get_reply

app = FastAPI()

# Allow the extension (chrome-extension://*), localhost (common dev host), and any additional
# origins to reach the backend. Credentials are enabled so the session cookie can flow.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://localhost:8000", "http://127.0.0.1:8000", "https://backend-j8gu.onrender.com"],
    allow_origin_regex=r"chrome-extension://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/create_session/{name}")
async def create_session(name: str, response: Response):
    session_id = uuid4()
    data = SessionData(username=name)

    await backend.create(session_id, data)
    cookie.attach_to_response(response, session_id)

    return {"ok": True, "session_id": str(session_id), "username": name}

@app.post("/questions")
async def get_questions(payload: QuestionIn | None = None, session: SessionContext = Depends(get_session_context)):
    # Accept either JSON body (preferred) or query param for backwards compatibility.
    question_number = payload.lc_question_number if payload else None
    question_title = payload.lc_question_title.strip() if payload and payload.lc_question_title else None
    if question_number is None:
        return {"ok": False, "error": "Missing lc_question_number"}

    title_fragment = f" titled '{question_title}'" if question_title else ""
    statement = (
        f"LeetCode Question #{question_number}: {title_fragment}. "
        f"Please identify and confirm the full title of this question, then gather and store all relevant details about it. "
        f"In your acknowledgment, respond with: Title of the question and 'How may I assist you further?'"
    )

    # Add the question statement into the chat state so future replies stay contextual.
    updated_session, reply = await apply_user_message_and_get_reply(
        session_id=session.id,
        session_data=session.data,
        user_text=statement,
    )

    await backend.update(session.id, updated_session)

    return {
        "ok": True,
        "res": reply,
        "message_count": len(updated_session.messages),
        "message_type": updated_session.message_type,
        "session_id": str(session.id),
    }

@app.get("/whoami")
async def whoami(session: SessionContext = Depends(get_session_context)):
    return session.data

@app.post("/chat")
async def chat(payload: ChatIn, session: SessionContext = Depends(get_session_context)):
    updated_session, reply = await apply_user_message_and_get_reply(
        session_id=session.id,
        session_data=session.data,
        user_text=payload.text,
    )

    await backend.update(session.id, updated_session)
    print(f"message type: {updated_session.message_type}")
    
    return {
        "reply": reply,
        "username": updated_session.username,
        "message_count": len(updated_session.messages),
        "message_type": updated_session.message_type,
    }


@app.post("/delete_session")
async def del_session(response: Response, session: SessionContext = Depends(get_session_context)):
    await backend.delete(session.id)
    cookie.delete_from_response(response)
    return {"ok": True}

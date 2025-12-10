from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field

Role = Literal["system", "user", "assistant"]


class StoredMessage(BaseModel):
    role: Role
    content: str
    ts: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SessionData(BaseModel):
    username: str
    messages: list[StoredMessage] = Field(default_factory=list)
    message_type: str | None = None
    auth_token: str

class QuestionIn(BaseModel):
    lc_question_number: int
    lc_question_title: str | None = None

class ChatIn(BaseModel):
    text: str

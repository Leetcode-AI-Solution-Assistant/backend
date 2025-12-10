from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, BaseMessage

from models import SessionData, StoredMessage
from state import State

def stored_to_lc(msg: StoredMessage) -> BaseMessage:
    if msg.role == "user":
        return HumanMessage(content=msg.content)
    if msg.role == "assistant":
        return AIMessage(content=msg.content)
    return SystemMessage(content=msg.content)

def lc_to_stored(msg: BaseMessage) -> StoredMessage:
    msg_type = getattr(msg, "type", None)  # "human" / "ai" / "system"
    if msg_type == "human":
        role = "user"
    elif msg_type == "ai":
        role = "assistant"
    else:
        role = "system"

    return StoredMessage(role=role, content=str(msg.content))

def session_to_state(sd: SessionData) -> State:
    return {
        "messages": [stored_to_lc(m) for m in sd.messages],
        "message_type": sd.message_type,
    }

def state_to_session(sd: SessionData, state: State) -> SessionData:
    sd.messages = [lc_to_stored(m) for m in state["messages"]]
    sd.message_type = state.get("message_type")
    return sd
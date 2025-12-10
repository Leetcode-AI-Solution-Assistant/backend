from __future__ import annotations

from uuid import UUID

from langchain_core.messages import HumanMessage

from ai import graph
from models import SessionData
from state_adapter import session_to_state, state_to_session
from state import State

async def run_graph(state: State) -> State:
    """Run the compiled LangGraph and return the new conversation state."""
    return await graph.ainvoke(state)


async def apply_user_message_and_get_reply(session_id: UUID, session_data: SessionData, user_text: str,) -> tuple[SessionData, str]:
    # session -> graph state
    state = session_to_state(session_data)

    # add user message into annotated state
    state["messages"] = state["messages"] + [HumanMessage(content=user_text)]

    # run graph
    new_state = await run_graph(state)

    # graph state -> session
    session_data = state_to_session(session_data, new_state)

    # get most recent assistant reply (best effort)
    last_reply = ""
    for msg in reversed(session_data.messages):
        if msg.role == "assistant":
            last_reply = msg.content
            break

    return session_data, last_reply

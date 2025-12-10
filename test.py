"""
Basic tests for the LangGraph pipeline defined in ai.py.

The real graph relies on a remote LLM. To keep tests fast and offline,
we stub out `init_chat_model` so the graph uses deterministic responses.
"""

from __future__ import annotations

import importlib
import sys

from langchain_core.messages import HumanMessage


class StubResult:
    def __init__(self, *, content: str | None = None, message_type: str | None = None):
        self.content = content
        self.message_type = message_type


class StubLLM:
    """LLM stub that returns queued responses for `.invoke` calls."""

    def __init__(self, responses: list[StubResult]):
        self._responses = list(responses)

    def with_structured_output(self, _schema):
        return self

    def invoke(self, *_args, **_kwargs):
        if not self._responses:
            raise AssertionError("StubLLM invoked more times than responses provided")
        return self._responses.pop(0)


def test_question_explanation_path(monkeypatch):
    """Graph should classify and reply with a question explanation."""
    stub = StubLLM(
        [
            StubResult(message_type="Question explanation"),  # planner classification
            StubResult(content="Here is the plain-English explanation."),  # node reply
        ]
    )

    # Reload ai with the stubbed init_chat_model so module-level graph builds offline.
    sys.modules.pop("ai", None)
    monkeypatch.setattr("langchain.chat_models.init_chat_model", lambda *_args, **_kwargs: stub)
    ai = importlib.import_module("ai")

    graph = ai.build_graph(model="stubbed")
    initial_state = {"messages": [HumanMessage(content="What does this problem ask?")], "message_type": None}

    result_state = graph.invoke(initial_state)

    assert result_state["message_type"] == "Question explanation"
    assert result_state["messages"][-1].content == "Here is the plain-English explanation."


def test_code_solution_path(monkeypatch):
    """Graph should route to code generation flow when classified accordingly."""
    stub = StubLLM(
        [
            StubResult(message_type="Code the solution as per user req/code correction"),
            StubResult(content="def solve():\n    pass"),
        ]
    )

    sys.modules.pop("ai", None)
    monkeypatch.setattr("langchain.chat_models.init_chat_model", lambda *_args, **_kwargs: stub)
    ai = importlib.import_module("ai")

    graph = ai.build_graph(model="stubbed")
    initial_state = {"messages": [HumanMessage(content="Write code for two sum in Python")], "message_type": None}

    result_state = graph.invoke(initial_state)

    assert result_state["message_type"] == "Code the solution as per user req/code correction"
    assert "def solve" in result_state["messages"][-1].content

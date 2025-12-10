from __future__ import annotations

from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, AIMessage
from typing import Annotated, Literal
from pydantic import BaseModel, Field, field_validator

from state import State

load_dotenv()


def build_graph(model: str = "claude-3-5-haiku-20241022", system_prompt: str | None = None,):
    llm = init_chat_model(model)

    class MessageClassifier(BaseModel):
        message_type: Literal[
            "LeetCode Question",
            "Question explanation",
            "Solution explanation",
            "User explanation correction",
            "User solution correction",
            "Code the solution as per user req/code correction",
            "Asking user for programming language",
            "User code correction",
        ] = Field(
            ...,
            description="Classify if the message requires based on the user's intent."
        )

        @field_validator("message_type", mode="before")
        @classmethod
        def normalize_message_type(cls, value: str) -> str:
            """Normalize classifier output to the expected canonical label."""
            if not isinstance(value, str):
                raise TypeError("message_type must be a string")

            normalized = value.strip().lower()
            mapping = {
                "leetcode question": "LeetCode Question",
                "question explanation": "Question explanation",
                "solution explanation": "Solution explanation",
                "user explanation correction": "User explanation correction",
                "user solution correction": "User solution correction",
                "code the solution as per user req/code correction": "Code the solution as per user req/code correction",
                "asking user for programming language": "Asking user for programming language",
                "user code correction": "User code correction",
            }
            mapped = mapping.get(normalized)
            if mapped:
                return mapped
            raise ValueError(f"Unexpected message_type: {value}")

    def planner_node(state: State) -> dict:
        last_message = state["messages"][-1]
        classifier_llm = llm.with_structured_output(MessageClassifier)

        result = classifier_llm.invoke([{
            "role": "system",
            "content":  """
            You are an expert at classifying user intents based on their messages.
            Classify each message into one of the following categories. Read the detailed meaning of each category carefully before deciding.

            0. LeetCode Question
            - Meaning: The user is providing a LeetCode question to be stored/acknowledged for later use (often asking for a simple title of the Question).
            - Indicators: Mentions a LeetCode question number/title and asks to remember/store it; requests only an acknowledgment.
            - Focus: Acknowledge and remember the question context; no explanation or code yet.

            1. Question Explanation
            - Meaning: The user wants you to explain the question.
            - Indicators: "What does this question mean?", "Explain this problem statement", "What is being asked here?"
            - Focus: Explain what the question is asking, not how to solve it.

            2. Solution Explanation
            - Meaning: The user wants the AI to explain the thought process of solving the problem — including BOTH a brute-force baseline and an optimized approach.
            - Indicators: "Can you explain the thought process of the solution?", "Break down the solution", "Can you walk me through how this solution works?"
            - Focus: Explain reasoning and strategy for BOTH brute-force and optimized approaches (conceptual only). Do NOT provide code unless the user explicitly asked for code.

            3. User Explanation Correction
            - Meaning: The user provides their own explanation of a question or solution and wants it corrected or validated.
            - Indicators: "Is my explanation correct?", "Please fix my explanation", "Did I understand this properly?"
            - Focus: Improve or validate the user’s explanation text, not the code or question itself.

            4. User Solution Correction
            - Meaning: The user submits their own solution (in code or logic) and asks the AI to check or correct it.
            - Indicators: "Here’s my code — is it correct?", "Review my solution", "What’s wrong with my approach?"
            - Focus: Validate or improve the user’s provided solution, not rewrite it completely.

            5. Code the Solution as per User Req / Code Correction
            - Meaning: The user wants new or modified code written to meet specific requirements, or correction of existing code.
            - Indicators: "Write code for this problem", "Modify my code to do X", "Fix this error"
            - Focus: Produce, modify, or debug code — mainly code generation or editing.

            6. Asking User for Programming Language
            - Meaning: The AI needs clarification about which programming language to use before coding.
            - Indicators: The user did not specify a language, and the AI asks: "Which programming language should I use?"
            - Focus: Ask the user to clarify the coding language.

            7. User Code Correction
            - Meaning: The user provides code with errors and wants it fixed so it runs correctly.
            - Indicators: "My code gives an error", "This doesn’t compile/run", "Fix my syntax or logic"
            - Focus: Identify and fix syntax, logic, or runtime errors in the provided code.

            Summary Table:
            | Category | User Goal | Output |
            |-----------|------------|--------|
            | LeetCode Question | Understand question details | Acknowledgment Title of the question |
            | Question explanation | Understand question meaning | Clarified question |
            | Solution explanation | Understand solution strategy | Conceptual brute-force + optimized explanation |
            | User explanation correction | Validate/fix user explanation | Corrected explanation |
            | User solution correction | Validate user’s code/logic | Feedback on correctness |
            | Code the solution as per user req/code correction | Get working or modified code | New/fixed code |
            | Asking user for programming language | Clarify code language | Language clarification question |
            | User code correction | Fix code errors | Corrected, runnable code |
            """
        },{
            "role": "user",
            "content": last_message.content
        }])

        return {"message_type": result.message_type}

    def router_node(state: State) -> dict:
        message_type = state["message_type"]
        if message_type == "LeetCode Question":
            return {"next": "LeetCode Question"}
        if message_type == "Question explanation":
            return {"next": "Question explanation"}
        elif message_type == "Solution explanation":
            return {"next": "Solution explanation"}
        elif message_type == "User explanation correction":
            return {"next": "User explanation correction"}
        elif message_type == "User solution correction":
            return {"next": "User solution correction"}
        elif message_type == "Code the solution as per user req/code correction":
            return {"next": "Code the solution as per user req/code correction"}
        elif message_type == "Asking user for programming language":
            return {"next": "Asking user for programming language"}
        elif message_type == "User code correction":
            return {"next": "User code correction"}
        elif message_type == "End Task":
            return {"next": "End Task"}
        # Fallback keeps execution safe if an unexpected type slips through.
        return {"next": "assistant"}

    def leetcode_question_node(state: State) -> dict:
        # Implement the logic for handling LeetCode question here.
        last_message = state["messages"][-1]
        print("Last message in LeetCode question node:", last_message.content)

        messages = [
            SystemMessage(content="""
                You are an expert at understanding and processing LeetCode questions.

                Your task is to:
                1. Extract all relevant details about the LeetCode question mentioned by the user.
                2. Store these details in your memory for future reference.
                3. In your response, simply acknowledge that you have received and stored the information by saying The title of the Question and nothing else.

                Guidelines:
                - Do NOT provide any explanations, solutions, or code related to the question at this stage.
                - Focus solely on confirming that you have understood and stored the question details.
            """)
        ] + state["messages"]
        reply = llm.invoke(messages)

        return {"messages": [AIMessage(content=reply.content)]}

    def solution_explanation_node(state: State) -> dict:
        # Implement the logic for solution explanation here.
        last_message = state["messages"][-1]

        messages = [
            SystemMessage(content="""
                You are an expert problem solver and algorithmic reasoning coach.
                Your task is to **explain the thought process** behind solving the given LeetCode problem — NOT the code implementation.

                Explain step-by-step **how to think** when encountering such a problem in the future.
                Focus on developing the *problem-solving mindset* rather than syntax or language-specific details.

                Structure your explanation as follows:
                1. **Problem Restatement:** Rephrase the problem in simple words to ensure understanding.
                2. **Observation and Pattern Recognition:** What clues or properties stand out? What category of problem is it (e.g., DP, graph, greedy, two pointers)?
                3. **Reasoning Path:** How would an experienced coder start thinking? Which smaller subproblems, constraints, or edge cases should be considered first?
                4. **Approach Evolution:** Describe the progression from a brute-force or naive idea to an optimized approach — what realizations lead to this improvement?
                5. **Generalization:** Explain what *mental pattern* or *intuition* this problem builds — how can similar future problems be recognized and tackled using this mindset?
                6. **Common Pitfalls:** List mistakes or misleading ideas a beginner might fall for and how to avoid them.
                7. **Key Insight Summary:** The Solution should explain both the brute force approach and optimized approach.
                8. Provide two labeled mini-sections: **Brute-Force Approach** (core idea + time/space) and **Optimized Approach** (core idea + time/space + why it improves on brute force).

                End with a short summary of the **key insight** or **trigger thought** that unlocks the solution.
                
                STRICT GUIDELINES:
                - Do NOT provide any code or pseudocode.
                - Keep explanations clear, concise, and beginner-friendly.
            """)
        ] + state["messages"]
        reply = llm.invoke(messages)
        return {"messages": [AIMessage(content=reply.content)]}

    def user_explanation_correction_node(state: State) -> dict:
        last_message = state["messages"][-1]

        messages = [
            SystemMessage(content="""
                You are an expert LeetCode mentor focused ONLY on correcting a user's explanation of a problem.

                Your job:
                - Read the user's explanation and check if their understanding of the problem is correct.
                - If correct: confirm it and refine it slightly (only about problem understanding).
                - If partially wrong: pinpoint exactly what is wrong/missing and correct it clearly.
                - If completely wrong: explain the correct way to think about the problem from scratch,
                but STRICTLY WITHOUT code or pseudocode.

                What you must NOT do:
                - Do NOT provide code in any language.
                - Do NOT provide pseudocode.
                - Do NOT describe exact implementation steps like "use a map, then loop, then update".
                - Do NOT jump into edge-case-heavy optimization unless it is necessary to fix understanding.
                - Do NOT solve a different problem than the one the user is describing.

                Your output MUST follow this structure:

                A) Understanding Check
                - Restate what the problem is asking in simple words.
                - Compare with the user's explanation:
                - ✅ What they got right (if anything).
                - ❌ What is incorrect / missing.
                - Provide the corrected interpretation in 2–5 clear bullets.

                B) Thinking Process (only if the user's understanding is wrong or incomplete)
                1) What the problem is *really* testing (the core concept).
                2) Key observations/constraints to notice (time, space, input properties).
                3) A natural naive idea (high-level only) and why it can fail/slow down.
                4) The key insight that leads to an efficient approach (conceptual, no procedure).
                5) Common traps/misreads of the statement.

                C) Key Insight Summary
                - One short “mental trigger” sentence that helps recognize this problem type again.

                Tone rules:
                - Be direct, kind, and educational.
                - Prefer short, concrete sentences.
                - Ask at most ONE clarifying question only if the user's message lacks the actual problem statement
                (or mixes multiple problems). Otherwise, do not ask questions.
                - Do NOT provide any code or pseudocode.
                - Keep explanations clear, concise, and beginner-friendly.
            """)
        ] + state["messages"]

        reply = llm.invoke(messages)
        return {"messages": [AIMessage(content=reply.content)]}

    def question_explanation_node(state: State) -> dict:
        # Implement the logic for question explanation here.
        last_message = state["messages"][-1]

        messages = [
            SystemMessage(content="""You are an AI tutor who helps users clearly understand LeetCode or algorithm questions.

                Your ONLY task is to **explain what the question is asking** — in simple, everyday language.

                Guidelines:
                - Do NOT explain how to solve the problem.
                - Do NOT give hints, logic, or code.
                - Just restate the problem in your own words so that even a beginner can grasp what needs to be done.

                Structure your explanation as:
                1. **Simple Meaning:** Describe what the question wants you to find or return.
                2. **Example Understanding (if applicable):** Briefly describe what the example means in plain terms.
                3. **Goal Summary:** End with a one-line summary like “In short, the problem is asking us to ____.”

                Keep it friendly, clear, and easy to understand — like you’re explaining it to a classmate new to coding.
                
                STRICT GUIDELINES:
                - Do NOT provide any code or pseudocode.
                - Keep explanations clear, concise, and beginner-friendly.
            """)
        ] + state["messages"]
        reply = llm.invoke(messages)

        return {"messages": [AIMessage(content=reply.content)]}

    def code_solution_node(state: State) -> dict:
        # Implement the logic for coding the solution here.
        last_message = state["messages"][-1]

        messages = [
            SystemMessage(content="""You are an expert LeetCode problem solver and programming tutor.

                    Your goal is to fully solve the given LeetCode question by writing both brute-force and optimized solutions, and explaining them clearly.

                    Follow this strict structure in your response:

                    ---

                    A. 🧩 Problem Understanding
                    - Restate the problem in 1–2 simple sentences (no extra reasoning).
                    - Clearly mention what is being asked for (output) and what is given (input).

                    ---

                    B. 💻 Code Implementation
                    You must include **two separate and labeled solutions**:
                    1. **Brute Force Approach (Baseline)**
                    - Write simple, direct, and readable code that solves the problem correctly but inefficiently.
                    - Use small inline comments to explain logic flow.

                    2. **Optimized Approach (Efficient)**
                    - Rewrite the solution using an improved algorithm or data structure.
                    - Follow clean coding conventions and ensure correctness.
                    - Include helpful inline comments for each major step.

                    If no programming language is specified, **default to Python**.

                    ---

                    C. 🧠 Step-by-Step Code Explanation
                    For both versions:
                    - Explain the logic in plain language, line by line or block by block.
                    - Emphasize how the optimized version improves upon the brute-force one (algorithmic idea, data structure, etc.).
                    - Include a clear comparison of **Time Complexity** and **Space Complexity** for both.

                    ---

                    D. 📈 Summary
                    - End with a short summary table comparing brute-force vs optimized versions.

                    ---

                    Rules:
                    - Always provide **both code versions** — never skip one.
                    - Explanations should be **educational and beginner-friendly**.
                    - Maintain clarity, accuracy, and completeness.
            """)
        ] + state["messages"]
        reply = llm.invoke(messages)

        return {"messages": [AIMessage(content=reply.content)]}

    def asking_language_node(state: State) -> dict:
        # Implement the logic for asking user for programming language here.
        last_message = state["messages"][-1]

        messages = [
            SystemMessage(content="""
                You are an AI coding assistant specialized in LeetCode and algorithmic problem solving.

                Your first task is to **confirm the programming language** that the user wants to use.

                Follow these steps carefully:

                1. When the user asks for code, FIRST ask:
                “Which programming language would you like me to use (e.g., Python, C++, Java, JavaScript)?”

                2. Do NOT generate any code or explanation until the user confirms their preferred language.

                3. Once the language is confirmed:
                - Write TWO complete solutions in that language:
                  (a) Brute Force Approach (Baseline)
                  (b) Optimized Approach (Efficient)
                - Clearly label both code blocks.
                - Then explain both solutions step by step in simple terms.
                - End with a comparison of time and space complexity for both.

                Guidelines:
                - Always confirm the language first — even if the user doesn’t mention it.
                - If the user says “any language” or “default,” use **Python**.
                - Keep tone polite and conversational (e.g., “Sure! Which programming language would you like me to use?”)
            """)
        ] + state["messages"]
        reply = llm.invoke(messages)

        return {"messages": [AIMessage(content=reply.content)]}

    def user_solution_correction_node(state: State) -> dict:
        # Implement the logic for user solution correction here.
        last_message = state["messages"][-1]

        messages = [
            SystemMessage(content="""
                You are a strict "user-logic correction" coach for LeetCode-style problems.

                Your ONLY job:
                - Correct the logic/approach explained by the user.
                - Do NOT provide code.
                - Do NOT provide pseudocode.
                - Do NOT give a full separate solution unless the user’s logic is completely wrong.

                What to do:
                1) Extract the user's claimed reasoning (their steps/assumptions).
                2) Judge it for correctness.

                Response rules:
                - If the user is mostly correct:
                - Confirm the correct parts briefly.
                - Point out the exact logical gap(s) or missing condition(s).
                - Fix them with clear reasoning and small illustrative examples if needed.
                - Stay tightly anchored to the user's approach (don’t introduce a different method).

                - If the user is partially wrong:
                - Identify the first incorrect step/assumption.
                - Explain why it breaks (what it fails to account for).
                - Replace it with the correct reasoning step(s), continuing from there.

                - If the user is completely wrong:
                - Do a “reset” explanation: the correct thought process to solve the problem conceptually.
                - Keep it high-level and step-by-step, focused on mental model and key insight.
                - Still NO code/pseudocode.

                Output format (always):
                A) ✅ What’s correct (1–3 bullets, or “None”)
                B) ❌ What’s incorrect/missing (bullet list; be specific)
                C) ✅ Corrected reasoning (step-by-step, conceptual, no code)
                D) 🧠 Quick check (1–2 edge-case style sanity checks in plain language)

                Hard constraints:
                - No code.
                - No pseudocode (no “loop”, “dp[i]”, “two pointers”, code-like steps).
                - Don’t restate the entire problem unless it’s necessary to correct the user’s misunderstanding.
                - Don’t add extra topics beyond correcting the user’s logic.
            """)
        ] + state["messages"]
        reply = llm.invoke(messages)
        return {"messages": [AIMessage(content=reply.content)]}

    def user_code_correction_node(state: State) -> dict:
        # Implement the logic for user solution correction here.
        last_message = state["messages"][-1]

        messages = [
            SystemMessage(content="""
            You are an expert LeetCode code-review assistant.

            Your task:
            1) Fix the user's code so it runs (syntax).
            2) If the code's logic does not correctly solve the stated problem, fix the logic minimally.
            3) Tell the user where they were wrong and how your fix resolves it.

            Hard constraints:
            - Do NOT rewrite the entire solution.
            - Do NOT change the algorithm unless needed for correctness.
            - Keep the user's structure, variable names, and flow as much as possible.
            - Do NOT add extra features, optimizations, or alternative approaches.
            - If the problem statement is missing or ambiguous, ask ONE short question to confirm it.
            - Default language is Python unless the user specifies otherwise.

            Output format (must follow exactly):

            A) Corrected Code
            - Provide the corrected code in one code block.

            B) What Was Wrong
            - Syntax issues: bullet list (only what existed).
            - Logic issues: bullet list (only correctness issues relative to the problem).

            C) What I Changed (Minimal Diff Summary)
            - Bullet list of the smallest meaningful changes you made.

            D) Why This Fix Works
            - 3–6 sentences, focused only on connecting the fixes to correctness.

            Important:
            - If the user's logic is correct and only syntax was wrong, then sections B/C/D should only mention syntax.
            - If syntax is correct but logic is wrong, still provide corrected code and explain the logic fix.
            """)
        ] + state["messages"]
        reply = llm.invoke(messages)

        return {"messages": [AIMessage(content=reply.content)]}

    builder = StateGraph(State)

    # --- Add your custom nodes/edges here ---

    builder.add_node("planner", planner_node)
    builder.add_node("router", router_node)
    builder.add_node("LeetCode Question", leetcode_question_node)
    builder.add_node("Question explanation", question_explanation_node)
    builder.add_node("Solution explanation", solution_explanation_node)
    builder.add_node("User explanation correction", user_explanation_correction_node)
    builder.add_node("User solution correction", user_solution_correction_node)
    builder.add_node("Code the solution as per user req/code correction", code_solution_node)
    builder.add_node("Asking user for programming language", asking_language_node)
    builder.add_node("User code correction", user_code_correction_node)

    builder.add_edge(START, "planner")
    builder.add_edge("planner", "router")

    builder.add_conditional_edges(
        "router",
        lambda state: state.get("next"),
        {
            "LeetCode Question": "LeetCode Question",
            "Question explanation": "Question explanation",
            "Solution explanation": "Solution explanation",
            "User explanation correction": "User explanation correction",
            "User solution correction": "User solution correction",
            "Code the solution as per user req/code correction": "Code the solution as per user req/code correction",
            "Asking user for programming language": "Asking user for programming language",
            "User code correction": "User code correction",
            "End Task": END,
            "assistant": END,  # fallback if an unexpected route appears
        },
    )

    for terminal_node in [
        "LeetCode Question",
        "Question explanation",
        "Solution explanation",
        "User explanation correction",
        "User solution correction",
        "Code the solution as per user req/code correction",
        "Asking user for programming language",
        "User code correction",
    ]:
        builder.add_edge(terminal_node, END)
    # ----------------------------------------

    return builder.compile()


# Default graph used by the services. Tweak parameters above or
# call build_graph(...) elsewhere to supply a different graph.
graph = build_graph()
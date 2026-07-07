"""L3 · Persistence ≠ memory — long-term, searchable memory.

State (L2) remembers *facts you set*. Memory remembers *what happened* — past
conversations you can search later. Here Sage recalls, in a brand-new session,
that Alice loved the lentil curry and disliked the mushroom risotto last week.

Per our POC: we don't hope the model reasons over raw recalled text — a
before_agent_callback searches memory and INJECTS the facts into state, which the
instruction then uses.

    uv run python -m L3_memory.demo
"""
import asyncio
import os

from dotenv import load_dotenv

load_dotenv()
os.environ.pop("GOOGLE_GENAI_USE_VERTEXAI", None)

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.memory import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from shared.harness import say
from shared.sage import MODEL, note_preference, suggest_meal


async def recall_into_state(callback_context: CallbackContext) -> None:
    """Before Sage answers, pull the user's food history from long-term memory
    and drop it into state so the instruction can use it.
    (ADK passes this as callback_context=... — the parameter name must match.)"""
    resp = await callback_context.search_memory("the user's food likes, dislikes and past meals")
    facts = []
    for m in resp.memories:
        if getattr(m, "content", None):
            facts.append(" ".join(p.text for p in m.content.parts if getattr(p, "text", None)))
    callback_context.state["recalled"] = " | ".join(facts) if facts else "(nothing remembered yet)"


def build_sage_with_recall() -> Agent:
    return Agent(
        name="sage", model=MODEL,
        instruction=(
            "You are Sage, a warm meal assistant. Here is what you remember about this "
            "user from past chats:\n{recalled}\n"
            "Use it: suggest things they liked, avoid things they disliked. "
            "Call suggest_meal when asked what to cook. Keep replies to 1–2 sentences."
        ),
        tools=[note_preference, suggest_meal],
        before_agent_callback=recall_into_state,
    )


async def main():
    session_service = InMemorySessionService()
    memory = InMemoryMemoryService()

    print("── Last week: Alice chats, then the session is saved to memory ──")
    from shared.sage import build_sage
    sage_plain = build_sage()
    r1 = Runner(agent=sage_plain, app_name="sage", session_service=session_service, memory_service=memory)
    await session_service.create_session(app_name="sage", user_id="alice", session_id="wk1")
    await say(r1, "wk1", "That lentil curry you suggested last week was amazing! But the "
                          "mushroom risotto — not for me, I really disliked it.")
    wk1 = await session_service.get_session(app_name="sage", user_id="alice", session_id="wk1")
    await memory.add_session_to_memory(wk1)
    print("   (session saved to long-term memory)\n")

    print("── This week: a NEW session — Sage recalls what happened ──")
    sage_recall = build_sage_with_recall()
    r2 = Runner(agent=sage_recall, app_name="sage", session_service=session_service, memory_service=memory)
    await session_service.create_session(app_name="sage", user_id="alice", session_id="wk2")
    await say(r2, "wk2", "Hey Sage, what should I cook tonight?")

    print("✅ Long-term memory: a fresh session recalled a fact from a PAST one — "
          "'persistence is not memory.'")


if __name__ == "__main__":
    asyncio.run(main())

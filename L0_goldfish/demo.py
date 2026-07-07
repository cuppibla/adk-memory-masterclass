"""L0 · The goldfish — no memory system at all.

Sage runs on an InMemorySessionService. Within one chat it's fine, but open a NEW
chat ("come back tomorrow") and Sage is a total stranger. Run from the repo root:

    uv run python -m L0_goldfish.demo
"""
import asyncio
import os

from dotenv import load_dotenv

load_dotenv()
os.environ.pop("GOOGLE_GENAI_USE_VERTEXAI", None)

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

from shared.harness import say
from shared.sage import build_sage


async def main():
    sage = build_sage()
    session_service = InMemorySessionService()
    runner = Runner(agent=sage, app_name="sage", session_service=session_service)

    print("── Chat A ──")
    await session_service.create_session(app_name="sage", user_id="alice", session_id="A")
    await say(runner, "A", "Hi! I'm Alice and I'm vegetarian.")

    print("── Chat B — a brand-new session ('coming back tomorrow') ──")
    await session_service.create_session(app_name="sage", user_id="alice", session_id="B")
    await say(runner, "B", "Hey Sage, what do you know about my diet?")

    print("❌ Goldfish: a new session is a total stranger. Sage needs a place to keep "
          "what it learns → that's the next rung.")


if __name__ == "__main__":
    asyncio.run(main())

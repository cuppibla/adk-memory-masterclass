"""L1 · The scratchpad — session.state.

Sage saves what you tell it into session.state. Within ONE conversation, turn 2
remembers turn 1. (But it's still one session — a new chat forgets. That's L2.)

    uv run python -m L1_scratchpad.demo
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
    sage = build_sage()   # its note_preference tool writes to tool_context.state
    session_service = InMemorySessionService()
    runner = Runner(agent=sage, app_name="sage", session_service=session_service)

    await session_service.create_session(app_name="sage", user_id="alice", session_id="A")
    print("── One conversation, two turns ──")
    await say(runner, "A", "I'm vegetarian, and please — no mushrooms.")
    await say(runner, "A", "Great — what should I make for dinner tonight?")

    s = await session_service.get_session(app_name="sage", user_id="alice", session_id="A")
    print(f"✅ session.state remembered across the turns: preferences = {s.state.get('preferences')}")


if __name__ == "__main__":
    asyncio.run(main())

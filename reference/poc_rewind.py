"""POC 2 — session rewind / undo (L5).
Proves: runner.rewind_async(rewind_before_invocation_id=...) rolls session state
back to before a given turn.
"""
import asyncio
import os

from dotenv import load_dotenv

load_dotenv()
os.environ.pop("GOOGLE_GENAI_USE_VERTEXAI", None)

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.adk.tools import ToolContext
from google.genai import types

MODEL = "gemini-3-flash-preview"


def set_plan(dish: str, tool_context: ToolContext) -> dict:
    """Set tonight's dinner plan to the given dish."""
    tool_context.state["plan"] = dish
    return {"status": "ok", "plan": dish}


sage = Agent(
    name="sage", model=MODEL,
    instruction="When the user names a dish for dinner, call set_plan with it. Be brief.",
    tools=[set_plan],
)


async def turn(runner, sid, text):
    inv = None
    async for ev in runner.run_async(
        user_id="u", session_id=sid,
        new_message=types.Content(role="user", parts=[types.Part(text=text)]),
    ):
        inv = ev.invocation_id
    return inv


async def plan_now(ss):
    s = await ss.get_session(app_name="sage", user_id="u", session_id="s")
    return s.state.get("plan")


async def main():
    runner = InMemoryRunner(agent=sage, app_name="sage")
    ss = runner.session_service
    await ss.create_session(app_name="sage", user_id="u", session_id="s")

    inv1 = await turn(runner, "s", "Let's plan lentil curry for tonight.")
    print(f"after turn 1: plan = {await plan_now(ss)!r}   (invocation {inv1})")

    inv2 = await turn(runner, "s", "Actually, change it to mushroom soup.")
    print(f"after turn 2: plan = {await plan_now(ss)!r}   (invocation {inv2})")

    print("--- rewind BEFORE turn 2 (undo the change) ---")
    await runner.rewind_async(user_id="u", session_id="s",
                              rewind_before_invocation_id=inv2)
    print(f"after rewind: plan = {await plan_now(ss)!r}   (should be back to 'lentil curry')")


if __name__ == "__main__":
    asyncio.run(main())

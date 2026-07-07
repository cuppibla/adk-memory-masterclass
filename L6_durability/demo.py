"""L6 · Surviving time — durability (pause & resume).

Where memory meets long-running work. Sage's grocery order is a
LongRunningFunctionTool: it pauses for the user's confirmation, the run ENDS, and
it resumes later when they confirm. (The full crash-and-restart story is Lab 1 —
loop-lab-onboarding; here we show the pause/resume in the memory context.)

    uv run python -m L6_durability.demo
"""
import asyncio
import os

from dotenv import load_dotenv

load_dotenv()
os.environ.pop("GOOGLE_GENAI_USE_VERTEXAI", None)

from google.adk.agents import Agent
from google.adk.apps.app import App, ResumabilityConfig
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import LongRunningFunctionTool, ToolContext
from google.genai import types

from shared.sage import MODEL


def order_groceries(items: str, tool_context: ToolContext) -> dict:
    """Place a grocery order. Needs the user to confirm before it goes through."""
    return {"status": "pending_confirmation", "items": items}


sage = Agent(
    name="sage", model=MODEL,
    instruction=("When the user asks to order groceries, call order_groceries with the items. "
                 "Once you receive a confirmation (confirmed=true), tell them the order is placed. "
                 "Be brief."),
    tools=[LongRunningFunctionTool(order_groceries)],
)
app = App(name="sage", root_agent=sage,
          resumability_config=ResumabilityConfig(is_resumable=True))


async def run(runner, sid, message):
    pending = None
    async for ev in runner.run_async(user_id="alice", session_id=sid, new_message=message):
        for f in ev.get_function_calls() or []:
            if ev.long_running_tool_ids and f.id in ev.long_running_tool_ids:
                pending = (f.id, f.name)
                print(f"       · order_groceries({dict(f.args)}) → PENDING (awaiting confirmation)")
        if ev.content and ev.content.parts:
            for p in ev.content.parts:
                if p.text and p.text.strip():
                    print(f"  🌿 {p.text.strip()}")
    return pending


async def main():
    session_service = InMemorySessionService()
    runner = Runner(app=app, session_service=session_service)
    await session_service.create_session(app_name="sage", user_id="alice", session_id="s")

    print("── Sage places an order — it pauses for confirmation, then the run ends ──")
    pending = await run(runner, "s", types.Content(role="user", parts=[types.Part(
        text="Order groceries for the lentil curry: lentils, onions, coconut milk.")]))
    print(f"  (the process is free; a pending order waits in the session: {pending})\n")

    print("── Later — the user confirms → the run resumes and completes ──")
    fid, fname = pending
    resume = types.Content(role="user", parts=[types.Part(
        function_response=types.FunctionResponse(
            id=fid, name=fname, response={"confirmed": True, "status": "placed"}))])
    await run(runner, "s", resume)

    print("✅ Durability: a long-running task paused, the run ended, and it resumed later on "
          "confirmation. Full crash/restart story → Lab 1 (loop-lab-onboarding).")


if __name__ == "__main__":
    asyncio.run(main())

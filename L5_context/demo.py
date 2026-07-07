"""L5 · Working memory — keeping a long conversation manageable.

Two tools for the context window (the agent's short-term "working memory"):
  • COMPACTION — long chats get summarized so they stay affordable.
  • REWIND     — undo a turn, rolling state back.
(Context CACHING is a third — mentioned in the codelab; it's a cost/latency
optimization that's transparent to the agent, so there's nothing visible to run.)

    uv run python -m L5_context.demo
"""
import asyncio
import os

from dotenv import load_dotenv

load_dotenv()
os.environ.pop("GOOGLE_GENAI_USE_VERTEXAI", None)

from google.adk.agents import Agent
from google.adk.apps.app import App, EventsCompactionConfig
from google.adk.apps.llm_event_summarizer import LlmEventSummarizer
from google.adk.models import Gemini
from google.adk.runners import InMemoryRunner, Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import ToolContext
from google.genai import types

from shared.harness import say
from shared.sage import MODEL


async def demo_compaction():
    print("========== COMPACTION: a long chat gets summarized ==========")
    chat = Agent(name="sage", model=MODEL, instruction="You are Sage. Answer in ONE short sentence.")
    app = App(
        name="sage", root_agent=chat,
        events_compaction_config=EventsCompactionConfig(
            compaction_interval=3, overlap_size=1,
            summarizer=LlmEventSummarizer(llm=Gemini(model=MODEL)),
        ),
    )
    ss = InMemorySessionService()
    runner = Runner(app=app, session_service=ss)
    await ss.create_session(app_name="sage", user_id="alice", session_id="s")
    for i in range(6):
        async for _ in runner.run_async(
            user_id="alice", session_id="s",
            new_message=types.Content(role="user",
                                      parts=[types.Part(text=f"Give me quick dinner idea #{i+1}.")]),
        ):
            pass
    s = await ss.get_session(app_name="sage", user_id="alice", session_id="s")
    comp = [e for e in s.events if getattr(getattr(e, "actions", None), "compaction", None)]
    print(f"  {len(s.events)} events in the session; {len(comp)} compaction summary(ies) created.")
    if comp:
        c = comp[0].actions.compaction
        content = getattr(c, "compacted_content", c)
        text = " ".join(p.text for p in content.parts if getattr(p, "text", None))
        print(f"  📝 first compaction summary (condenses the earlier turns):\n     {text[:220]}…")
    print()


async def demo_rewind():
    print("========== REWIND: undo the last change ==========")

    def set_plan(dish: str, tool_context: ToolContext) -> dict:
        """Set tonight's dinner plan to the given dish."""
        tool_context.state["plan"] = dish
        return {"status": "ok", "plan": dish}

    sage = Agent(name="sage", model=MODEL, tools=[set_plan],
                 instruction="When the user names a dinner dish, call set_plan. Be brief.")
    runner = InMemoryRunner(agent=sage, app_name="sage")
    ss = runner.session_service
    await ss.create_session(app_name="sage", user_id="alice", session_id="s")

    inv = None
    async for ev in runner.run_async(user_id="alice", session_id="s",
        new_message=types.Content(role="user", parts=[types.Part(text="Let's plan lentil curry tonight.")])):
        pass
    async for ev in runner.run_async(user_id="alice", session_id="s",
        new_message=types.Content(role="user", parts=[types.Part(text="Actually, change it to mushroom soup.")])):
        inv = ev.invocation_id
    plan = (await ss.get_session(app_name="sage", user_id="alice", session_id="s")).state.get("plan")
    print(f"  plan after 'change it to mushroom soup' = {plan!r}")
    await runner.rewind_async(user_id="alice", session_id="s", rewind_before_invocation_id=inv)
    plan = (await ss.get_session(app_name="sage", user_id="alice", session_id="s")).state.get("plan")
    print(f"  plan after rewind = {plan!r}   ✅ (undone — back to lentil curry)")


async def main():
    await demo_compaction()
    await demo_rewind()


if __name__ == "__main__":
    asyncio.run(main())

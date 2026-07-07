"""POC 3 — context compaction (L5).
Runs a long conversation with EventsCompactionConfig and inspects WHERE the
compaction summary lands, so the lab can show it.
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
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

MODEL = "gemini-3-flash-preview"

sage = Agent(name="sage", model=MODEL,
             instruction="You are Sage, a meal assistant. Answer in ONE short sentence.")

app = App(
    name="sage", root_agent=sage,
    events_compaction_config=EventsCompactionConfig(
        compaction_interval=3,          # compact every 3 events
        overlap_size=1,
        summarizer=LlmEventSummarizer(llm=Gemini(model=MODEL)),
    ),
)


async def main():
    ss = InMemorySessionService()
    runner = Runner(app=app, session_service=ss)
    await ss.create_session(app_name="sage", user_id="u", session_id="s")

    for i in range(8):
        async for _ in runner.run_async(
            user_id="u", session_id="s",
            new_message=types.Content(role="user",
                                      parts=[types.Part(text=f"Give me quick dinner idea #{i+1}.")]),
        ):
            pass

    s = await ss.get_session(app_name="sage", user_id="u", session_id="s")
    print(f"total events in session: {len(s.events)}")

    # 1) any compaction on the session object itself?
    for attr in dir(s):
        if "compact" in attr.lower():
            print(f"  session.{attr} = {getattr(s, attr)!r}")

    # 2) any compaction markers on events?
    found = False
    for i, ev in enumerate(s.events):
        acts = getattr(ev, "actions", None)
        comp = getattr(acts, "compaction", None) if acts else None
        ev_comp = getattr(ev, "compaction", None)
        if comp or ev_comp:
            found = True
            summary = comp or ev_comp
            txt = getattr(summary, "compacted_content", summary)
            print(f"  event[{i}] author={ev.author} → COMPACTION: {str(txt)[:200]}")
    if not found:
        print("  (no compaction attr found on events; checking event fields for 'compact')")
        sample = s.events[0]
        print("  event fields:", [f for f in sample.model_fields if "compact" in f.lower()] or list(sample.model_fields.keys()))
        # dump actions fields
        if getattr(sample, "actions", None):
            print("  actions fields:", [f for f in sample.actions.model_fields])


if __name__ == "__main__":
    asyncio.run(main())

"""POC 1 — long-term memory round-trip (L3: 'persistence is not memory').
Proves: add_session_to_memory(session) then search_memory(...) recalls a fact from
a PAST session, and an agent can recall it in a NEW session via tool_context.search_memory.
"""
import asyncio
import os

from dotenv import load_dotenv

load_dotenv()
os.environ.pop("GOOGLE_GENAI_USE_VERTEXAI", None)

from google.adk.agents import Agent
from google.adk.memory import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import ToolContext
from google.genai import types

MODEL = "gemini-3-flash-preview"


async def say(runner, sid, text):
    reply = ""
    async for ev in runner.run_async(
        user_id="u", session_id=sid,
        new_message=types.Content(role="user", parts=[types.Part(text=text)]),
    ):
        for f in ev.get_function_calls() or []:
            print(f"      (tool: {f.name}({dict(f.args)}))")
        if ev.content and ev.content.parts:
            for p in ev.content.parts:
                if p.text:
                    reply += p.text
    return reply.strip()


async def main():
    ss = InMemorySessionService()
    mem = InMemoryMemoryService()

    print("=== A) raw round-trip: session 1 → add_session_to_memory → search_memory ===")
    sage = Agent(name="sage", model=MODEL,
                 instruction="You are Sage, a friendly meal assistant. Be brief.")
    runner = Runner(agent=sage, app_name="sage", session_service=ss, memory_service=mem)
    await ss.create_session(app_name="sage", user_id="u", session_id="s1")
    await say(runner, "s1",
              "Remember for later: I loved the lentil curry last week, and I really dislike mushrooms.")
    s1 = await ss.get_session(app_name="sage", user_id="u", session_id="s1")
    await mem.add_session_to_memory(s1)
    print(f"  added session 1 ({len(s1.events)} events) to long-term memory")
    resp = await mem.search_memory(app_name="sage", user_id="u",
                                   query="how does the user feel about mushrooms?")
    print(f"  search_memory → {len(resp.memories)} memory entries:")
    for m in resp.memories:
        txt = " ".join(p.text for p in m.content.parts if getattr(p, "text", None)) \
              if getattr(m, "content", None) else str(m)
        print(f"    • {txt[:180]}")

    print("\n=== B) a NEW session: agent recalls via tool_context.search_memory ===")

    async def recall_preferences(query: str, tool_context: ToolContext) -> dict:
        """Look up the user's past food likes/dislikes from long-term memory."""
        r = await tool_context.search_memory(query)
        facts = [" ".join(p.text for p in m.content.parts if getattr(p, "text", None))
                 for m in r.memories if getattr(m, "content", None)]
        return {"remembered": facts}

    sage2 = Agent(
        name="sage", model=MODEL,
        instruction=("You are Sage. BEFORE recommending a dish, call recall_preferences to "
                     "check the user's past likes/dislikes, then advise accordingly. Be brief."),
        tools=[recall_preferences],
    )
    runner2 = Runner(agent=sage2, app_name="sage", session_service=ss, memory_service=mem)
    await ss.create_session(app_name="sage", user_id="u", session_id="s2")
    reply = await say(runner2, "s2", "I'm thinking mushroom soup for dinner tonight — good idea?")
    print(f"  Sage: {reply}")


if __name__ == "__main__":
    asyncio.run(main())

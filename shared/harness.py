"""Tiny helper so each level's demo stays short: run one turn, print it."""
from google.genai import types


async def say(runner, session_id, text, user_id="alice", show_tools=True):
    reply = ""
    async for ev in runner.run_async(
        user_id=user_id, session_id=session_id,
        new_message=types.Content(role="user", parts=[types.Part(text=text)]),
    ):
        if show_tools:
            for f in ev.get_function_calls() or []:
                print(f"       · (Sage used {f.name}({dict(f.args)}))")
        if ev.content and ev.content.parts:
            for p in ev.content.parts:
                if p.text:
                    reply += p.text
    reply = reply.strip()
    print(f"  🧑 {text}")
    print(f"  🌿 {reply}\n")
    return reply

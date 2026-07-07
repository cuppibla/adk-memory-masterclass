"""L2 · Remember across restarts — DatabaseSessionService + the `user:` scope.

Two ideas at once:
  • DatabaseSessionService persists state to disk (survives a process restart).
  • the `user:` prefix scopes state to the USER, so it's shared across all their
    sessions — a new chat tomorrow still knows Alice.

    uv run python -m L2_persistence.demo
"""
import asyncio
import os

from dotenv import load_dotenv

load_dotenv()
os.environ.pop("GOOGLE_GENAI_USE_VERTEXAI", None)

from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.adk.tools import ToolContext

from shared.harness import say
from shared.recipes import pick
from shared.sage import build_sage

DB = "sqlite+aiosqlite:///./sage_l2.db"


# user-scoped versions of Sage's tools: note the "user:" prefix
def note_preference(preference: str, tool_context: ToolContext) -> dict:
    """Save a food preference for this USER (persists across all their sessions)."""
    prefs = list(tool_context.state.get("user:preferences", []))
    if preference not in prefs:
        prefs.append(preference)
    tool_context.state["user:preferences"] = prefs
    return {"status": "saved to user scope", "preferences": prefs}


def suggest_meal(tool_context: ToolContext) -> dict:
    """Suggest a meal honoring the user's saved (user-scoped) preferences."""
    prefs = tool_context.state.get("user:preferences", [])
    r = pick(prefs)
    return {"suggestion": r["name"], "considering": prefs}


async def main():
    if os.path.exists("sage_l2.db"):
        os.remove("sage_l2.db")
    sage = build_sage(tools=[note_preference, suggest_meal])

    print("── Monday: Alice tells Sage her preferences ──")
    svc1 = DatabaseSessionService(db_url=DB)
    runner1 = Runner(agent=sage, app_name="sage", session_service=svc1)
    await svc1.create_session(app_name="sage", user_id="alice", session_id="mon")
    await say(runner1, "mon", "Hi Sage — please remember I'm vegetarian and I love quick meals.")

    print("── Tuesday: a FRESH service + new session (as if the server restarted) ──")
    svc2 = DatabaseSessionService(db_url=DB)              # new process would look like this
    runner2 = Runner(agent=sage, app_name="sage", session_service=svc2)
    await svc2.create_session(app_name="sage", user_id="alice", session_id="tue")
    await say(runner2, "tue", "Morning! What should I cook for dinner tonight?")

    print("✅ The `user:` scope + DatabaseSessionService: a brand-new session on a fresh "
          "service still knows Alice is vegetarian.")


if __name__ == "__main__":
    asyncio.run(main())

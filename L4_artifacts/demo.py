"""L4 · Remembering files — artifacts.

State and memory hold facts and text. Artifacts hold *files* — a generated meal
plan, a shopping list PDF, an image. Sage saves a plan as a user-scoped artifact
and re-opens it in a brand-new session.

    uv run python -m L4_artifacts.demo
"""
import asyncio
import os

from dotenv import load_dotenv

load_dotenv()
os.environ.pop("GOOGLE_GENAI_USE_VERTEXAI", None)

from google.adk.agents import Agent
from google.adk.artifacts import InMemoryArtifactService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import ToolContext
from google.genai import types

from shared.harness import say
from shared.sage import MODEL

PLAN_FILE = "user:meal_plan.txt"   # "user:" → scoped to the user, survives across sessions


async def save_meal_plan(dishes: str, tool_context: ToolContext) -> dict:
    """Save the week's meal plan (a comma-separated list of dishes) as a file."""
    part = types.Part(inline_data=types.Blob(mime_type="text/plain", data=dishes.encode()))
    version = await tool_context.save_artifact(PLAN_FILE, part)
    return {"status": "saved", "file": PLAN_FILE, "version": version}


async def load_meal_plan(tool_context: ToolContext) -> dict:
    """Re-open the user's previously saved meal plan file."""
    art = await tool_context.load_artifact(PLAN_FILE)
    if not art or not art.inline_data:
        return {"status": "no_plan_found"}
    return {"status": "ok", "plan": art.inline_data.data.decode()}


sage = Agent(
    name="sage", model=MODEL,
    instruction=(
        "You are Sage. When the user asks you to plan and save meals, pick 3 dishes and call "
        "save_meal_plan with them as a comma-separated string. When they ask what their saved "
        "plan was, call load_meal_plan and read it back. Be brief."
    ),
    tools=[save_meal_plan, load_meal_plan],
)


async def main():
    session_service = InMemorySessionService()
    artifacts = InMemoryArtifactService()
    runner = Runner(agent=sage, app_name="sage",
                    session_service=session_service, artifact_service=artifacts)

    print("── Session 1: make + save a plan (writes a file) ──")
    await session_service.create_session(app_name="sage", user_id="alice", session_id="s1")
    await say(runner, "s1", "Plan me 3 quick vegetarian dinners for this week and save it.")

    print("── Session 2 (brand new): re-open the saved file ──")
    await session_service.create_session(app_name="sage", user_id="alice", session_id="s2")
    await say(runner, "s2", "Remind me — what was my saved meal plan?")

    print("✅ Artifacts: the generated plan file persisted (user scope) and re-loaded in a new "
          "session. In production, swap InMemoryArtifactService → GcsArtifactService.")


if __name__ == "__main__":
    asyncio.run(main())

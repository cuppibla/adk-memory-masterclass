"""L7 · Managed in the cloud — Vertex sessions + Memory Bank.

The payoff of the whole hierarchy: the Sage CODE doesn't change to go to
production. Only the SERVICES swap — from local ones to fully managed Vertex ones.
This is the optional cloud upgrade; everything else in the masterclass runs with
no cloud at all.

    # local (L2/L3)                    # managed (L7)
    DatabaseSessionService     →   VertexAiSessionService(project, location, agent_engine_id)
    InMemoryMemoryService      →   VertexAiMemoryBankService(project, location, agent_engine_id)
    → managed sessions + Memory Bank, nothing to run or back up.

    uv run python -m L7_managed.demo
"""
import asyncio
import os

from dotenv import load_dotenv

load_dotenv()

from shared.sage import build_sage


def build_managed_runner():
    """Same Sage, wired to managed Vertex services. Requires a GCP project + an
    Agent Engine instance (its id → AGENT_ENGINE_ID)."""
    from google.adk.memory import VertexAiMemoryBankService
    from google.adk.runners import Runner
    from google.adk.sessions import VertexAiSessionService

    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
    agent_engine_id = os.environ.get("AGENT_ENGINE_ID")

    session_service = VertexAiSessionService(
        project=project, location=location, agent_engine_id=agent_engine_id)
    memory_service = VertexAiMemoryBankService(
        project=project, location=location, agent_engine_id=agent_engine_id)
    return Runner(agent=build_sage(), app_name="sage",
                  session_service=session_service, memory_service=memory_service)


async def main():
    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    agent_engine_id = os.environ.get("AGENT_ENGINE_ID")

    print("L7 is the OPTIONAL managed upgrade — the Sage code is unchanged, only the services swap:")
    print("  DatabaseSessionService  →  VertexAiSessionService(project, location, agent_engine_id)")
    print("  InMemoryMemoryService   →  VertexAiMemoryBankService(project, location, agent_engine_id)\n")

    if not (project and agent_engine_id):
        print("⏭  Skipping the live run (no cloud configured). To run it:")
        print("   1) set GOOGLE_GENAI_USE_VERTEXAI=True, GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION")
        print("   2) create an Agent Engine instance and set AGENT_ENGINE_ID to its id")
        print("   Everything else in this masterclass runs with NO cloud — L7 is the production upgrade.")
        return

    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
    runner = build_managed_runner()
    ss = runner.session_service
    await ss.create_session(app_name="sage", user_id="alice", session_id="s")
    from shared.harness import say
    await say(runner, "s", "Hi Sage, I'm vegetarian — please remember that.")
    print("✅ Same Sage, now on managed Vertex sessions + Memory Bank (no infra to run).")


if __name__ == "__main__":
    asyncio.run(main())

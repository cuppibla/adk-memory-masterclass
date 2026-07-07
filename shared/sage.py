"""Sage — the shared base used by every level.

The *tools* and instruction don't change from level to level; what changes is the
MEMORY WIRING around Sage (which session service, whether there's long-term memory,
compaction, etc.). Each level imports from here and changes only that wiring.
"""
from google.adk.agents import Agent
from google.adk.tools import ToolContext

from .recipes import pick

MODEL = "gemini-3-flash-preview"

SAGE_INSTRUCTION = (
    "You are Sage, a warm and concise meal-planning assistant.\n"
    "- When the user shares a food preference or restriction (vegetarian, no mushrooms, "
    "quick meals, on a budget…), call note_preference to save it.\n"
    "- When the user asks what to cook/eat, call suggest_meal.\n"
    "- Keep replies to one or two friendly sentences."
)


def note_preference(preference: str, tool_context: ToolContext) -> dict:
    """Save a food preference or restriction for this user (e.g. 'vegetarian', 'no mushrooms')."""
    prefs = list(tool_context.state.get("preferences", []))
    if preference not in prefs:
        prefs.append(preference)
    tool_context.state["preferences"] = prefs
    return {"status": "saved", "preferences": prefs}


def suggest_meal(tool_context: ToolContext) -> dict:
    """Suggest a meal that respects the user's saved preferences."""
    prefs = tool_context.state.get("preferences", [])
    r = pick(prefs)
    return {"suggestion": r["name"], "minutes": r["minutes"], "considering": prefs}


def build_sage(tools=None, **agent_kwargs) -> Agent:
    """Make a Sage agent. Levels pass extra kwargs (e.g. before_agent_callback) as needed."""
    return Agent(
        name="sage",
        model=MODEL,
        instruction=agent_kwargs.pop("instruction", SAGE_INSTRUCTION),
        tools=tools if tools is not None else [note_preference, suggest_meal],
        **agent_kwargs,
    )

"""Assemble the two self-contained Colab notebooks from the tested code.

    uv run python notebooks/build.py

Produces notebooks/Sage_memory_1_remembering.ipynb (L0–L4) and
notebooks/Sage_memory_2_managing.ipynb (L5–L7). Each is self-contained: a setup
cell, the shared Sage base inlined, then one section per level. Code mirrors the
tested `Lx/demo.py` modules.
"""
import os

import nbformat as nbf


def md(t):
    return nbf.v4.new_markdown_cell(t.strip("\n"))


def code(t):
    return nbf.v4.new_code_cell(t.strip("\n"))


SETUP_MD = '''
### ⚙️ Setup — your Gemini API key

This masterclass runs on the **Gemini API** with a free **Google AI Studio** key.

1. Get a key at **[aistudio.google.com/apikey](https://aistudio.google.com/apikey)** — it's free and usually starts with `AIza…`.
2. **Recommended — Colab Secrets:** click the **🔑** icon in the left sidebar → **＋ Add new secret**, name it exactly `GOOGLE_API_KEY`, paste your key as the value, and turn **Notebook access** *on*. The cell below finds it automatically.
3. **No Secret?** Just run the cell — it will prompt you to paste the key (it isn't saved).

> 🔒 Treat the key like a password — don't paste it into shared docs or commit it to git.
'''

SETUP = '''
# @title ⚙️ Setup — install ADK and load your Gemini (AI Studio) API key  { display-mode: "form" }
# Key from https://aistudio.google.com/apikey  ·  add it to Colab Secrets as GOOGLE_API_KEY.
!pip install -q "google-adk[db]==2.3.0" aiosqlite greenlet
import os
try:
    from google.colab import userdata                 # Colab Secrets (recommended)
    os.environ["GOOGLE_API_KEY"] = userdata.get("GOOGLE_API_KEY")
except Exception:
    if not os.environ.get("GOOGLE_API_KEY"):           # else fall back to a prompt
        import getpass
        os.environ["GOOGLE_API_KEY"] = getpass.getpass("Paste your Gemini API key (AIza…): ")

# This masterclass talks to the Gemini API (AI Studio), not Vertex AI.
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"

key = os.environ.get("GOOGLE_API_KEY", "")
assert key, "No GOOGLE_API_KEY found — add it to Colab Secrets (🔑) or paste it when prompted."
if len(key) < 20:
    print("⚠️  That key looks too short — make sure you pasted the whole thing.")
print("✅ Ready — Sage is using the Gemini API (AI Studio).")
'''

SHARED = '''
# @title 🌿 Meet Sage — the shared base (tools + canned recipes + a tiny run helper)
# The *tools* don't change from level to level; only the MEMORY WIRING around Sage does.
from google.adk.agents import Agent
from google.adk.tools import ToolContext
from google.genai import types

MODEL = "gemini-3-flash-preview"

RECIPES = [
    {"name": "lentil curry",     "tags": ["vegetarian","budget","hearty"], "minutes": 30, "contains": []},
    {"name": "black bean tacos", "tags": ["vegetarian","budget","quick"],  "minutes": 20, "contains": []},
    {"name": "mushroom risotto", "tags": ["vegetarian","cozy"],            "minutes": 40, "contains": ["mushroom"]},
    {"name": "grilled salmon bowl","tags": ["pescatarian","healthy"],      "minutes": 25, "contains": ["fish"]},
    {"name": "chicken fajitas",  "tags": ["quick","budget"],               "minutes": 25, "contains": ["chicken"]},
]

def pick(preferences):
    prefs = " ".join(preferences).lower()
    for r in RECIPES:
        if "vegetarian" in prefs and "vegetarian" not in r["tags"]: continue
        if "quick" in prefs and "quick" not in r["tags"]: continue
        if any(bad in prefs for bad in r["contains"]): continue
        return r
    return RECIPES[0]

def note_preference(preference: str, tool_context: ToolContext) -> dict:
    """Save a food preference or restriction (e.g. 'vegetarian', 'no mushrooms')."""
    prefs = list(tool_context.state.get("preferences", []))
    if preference not in prefs: prefs.append(preference)
    tool_context.state["preferences"] = prefs
    return {"status": "saved", "preferences": prefs}

def suggest_meal(tool_context: ToolContext) -> dict:
    """Suggest a meal that respects the user's saved preferences."""
    prefs = tool_context.state.get("preferences", [])
    r = pick(prefs)
    return {"suggestion": r["name"], "minutes": r["minutes"], "considering": prefs}

SAGE_INSTRUCTION = (
    "You are Sage, a warm, concise meal-planning assistant. "
    "When the user shares a food preference, call note_preference. "
    "When they ask what to eat, call suggest_meal. Keep replies to 1-2 sentences."
)

def build_sage(tools=None, **kw):
    return Agent(name="sage", model=MODEL,
                 instruction=kw.pop("instruction", SAGE_INSTRUCTION),
                 tools=tools if tools is not None else [note_preference, suggest_meal], **kw)

async def say(runner, session_id, text, user_id="alice"):
    reply = ""
    async for ev in runner.run_async(user_id=user_id, session_id=session_id,
        new_message=types.Content(role="user", parts=[types.Part(text=text)])):
        for f in ev.get_function_calls() or []:
            print(f"       · (Sage used {f.name}({dict(f.args)}))")
        if ev.content and ev.content.parts:
            for p in ev.content.parts:
                if p.text: reply += p.text
    print(f"  🧑 {text}\\n  🌿 {reply.strip()}\\n")
    return reply.strip()

print("🌿 Sage is ready")
'''

# ---- level sections: (markdown intro, code cell) ----

L0 = (r'''
## L0 · The goldfish 🐟

Most agents are goldfish: open a new chat and they've forgotten you completely.
Sage here runs on an `InMemorySessionService` — within one chat it's fine, but a
**new session** ("come back tomorrow") is a total stranger.

*Watch it forget:*
''', r'''
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

sage = build_sage()
ss = InMemorySessionService()
runner = Runner(agent=sage, app_name="sage", session_service=ss)

print("── Chat A ──")
await ss.create_session(app_name="sage", user_id="alice", session_id="A")
await say(runner, "A", "Hi! I'm Alice and I'm vegetarian.")

print("── Chat B — a brand-new session ──")
await ss.create_session(app_name="sage", user_id="alice", session_id="B")
await say(runner, "B", "Hey Sage, what do you know about my diet?")
print("❌ A new session is a stranger. Sage needs somewhere to keep what it learns.")
''')

L1 = (r'''
## L1 · The scratchpad — `session.state` 📝

The simplest memory: a scratchpad that lives for one conversation. When Sage
learns something it writes to `session.state`; within that chat, later turns can
read it.

*Turn 2 remembers turn 1:*
''', r'''
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

sage = build_sage()   # note_preference writes to tool_context.state
ss = InMemorySessionService()
runner = Runner(agent=sage, app_name="sage", session_service=ss)
await ss.create_session(app_name="sage", user_id="alice", session_id="A")

await say(runner, "A", "I'm vegetarian, and please — no mushrooms.")
await say(runner, "A", "Great — what should I make for dinner tonight?")

s = await ss.get_session(app_name="sage", user_id="alice", session_id="A")
print(f"✅ session.state remembered across turns: {s.state.get('preferences')}")
''')

L2 = (r'''
## L2 · Remember across restarts — `DatabaseSessionService` + the `user:` scope 💾

Two ideas: a **database** session service persists state to disk (survives a
restart), and the **`user:`** prefix scopes state to the *user* — shared across
all their sessions. So a new chat tomorrow still knows Alice.

*A fresh service + new session still knows her:*
''', r'''
import os
from google.adk.runners import Runner
from google.adk.sessions import DatabaseSessionService
from google.adk.tools import ToolContext

DB = "sqlite+aiosqlite:///./sage_l2.db"
if os.path.exists("sage_l2.db"): os.remove("sage_l2.db")

def note_preference(preference: str, tool_context: ToolContext) -> dict:
    """Save a food preference for this USER (persists across all their sessions)."""
    prefs = list(tool_context.state.get("user:preferences", []))
    if preference not in prefs: prefs.append(preference)
    tool_context.state["user:preferences"] = prefs          # note the user: prefix
    return {"status": "saved to user scope", "preferences": prefs}

def suggest_meal(tool_context: ToolContext) -> dict:
    """Suggest a meal honoring the user's (user-scoped) preferences."""
    r = pick(tool_context.state.get("user:preferences", []))
    return {"suggestion": r["name"], "considering": tool_context.state.get("user:preferences", [])}

sage = build_sage(tools=[note_preference, suggest_meal])

print("── Monday ──")
svc1 = DatabaseSessionService(db_url=DB)
r1 = Runner(agent=sage, app_name="sage", session_service=svc1)
await svc1.create_session(app_name="sage", user_id="alice", session_id="mon")
await say(r1, "mon", "Hi Sage — remember I'm vegetarian and I love quick meals.")

print("── Tuesday: a FRESH service + new session (as if the server restarted) ──")
svc2 = DatabaseSessionService(db_url=DB)
r2 = Runner(agent=sage, app_name="sage", session_service=svc2)
await svc2.create_session(app_name="sage", user_id="alice", session_id="tue")
await say(r2, "tue", "Morning! What should I cook for dinner tonight?")
print("✅ user: scope + a database → a new session on a fresh service still knows Alice.")
''')

L3 = (r'''
## L3 · Persistence ≠ memory 🧠

State remembers *facts you set*. **Memory** remembers *what happened* — past
conversations you can search later. We save a session to long-term memory, then in
a brand-new session a `before_agent_callback` searches memory and **injects** the
recalled facts into state (so the model reliably uses them — don't hope it reasons
over raw text).

*A new session recalls a past meal:*
''', r'''
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.memory import InMemoryMemoryService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

ss = InMemorySessionService(); memory = InMemoryMemoryService()

print("── Last week: Alice chats, then the session is saved to memory ──")
r1 = Runner(agent=build_sage(), app_name="sage", session_service=ss, memory_service=memory)
await ss.create_session(app_name="sage", user_id="alice", session_id="wk1")
await say(r1, "wk1", "That lentil curry was amazing! But the mushroom risotto — I really disliked it.")
wk1 = await ss.get_session(app_name="sage", user_id="alice", session_id="wk1")
await memory.add_session_to_memory(wk1)          # distill the session into long-term memory

# the callback param MUST be named callback_context (ADK passes it as a keyword)
async def recall_into_state(callback_context: CallbackContext) -> None:
    resp = await callback_context.search_memory("the user's food likes, dislikes and past meals")
    facts = [" ".join(p.text for p in m.content.parts if getattr(p,'text',None))
             for m in resp.memories if getattr(m,'content',None)]
    callback_context.state["recalled"] = " | ".join(facts) or "(nothing yet)"

sage_recall = Agent(name="sage", model=MODEL, before_agent_callback=recall_into_state,
    tools=[note_preference, suggest_meal],
    instruction="You are Sage. Here's what you remember about this user:\\n{recalled}\\n"
                "Suggest things they liked, avoid things they disliked. Be brief.")

print("── This week: a NEW session — Sage recalls what happened ──")
r2 = Runner(agent=sage_recall, app_name="sage", session_service=ss, memory_service=memory)
await ss.create_session(app_name="sage", user_id="alice", session_id="wk2")
await say(r2, "wk2", "Hey Sage, what should I cook tonight?")
print("✅ Long-term memory: a fresh session recalled a fact from a PAST one.")
''')

L4 = (r'''
## L4 · Remembering files — artifacts 📎

State and memory hold text. **Artifacts** hold *files* — a meal plan, a PDF, an
image. Sage saves a plan as a `user:`-scoped artifact and re-opens it in a new
session. (In production, swap `InMemoryArtifactService` → `GcsArtifactService`.)
''', r'''
from google.adk.agents import Agent
from google.adk.artifacts import InMemoryArtifactService
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import ToolContext

PLAN_FILE = "user:meal_plan.txt"

async def save_meal_plan(dishes: str, tool_context: ToolContext) -> dict:
    """Save the week's meal plan (comma-separated dishes) as a file."""
    part = types.Part(inline_data=types.Blob(mime_type="text/plain", data=dishes.encode()))
    v = await tool_context.save_artifact(PLAN_FILE, part)
    return {"status": "saved", "file": PLAN_FILE, "version": v}

async def load_meal_plan(tool_context: ToolContext) -> dict:
    """Re-open the user's saved meal plan file."""
    art = await tool_context.load_artifact(PLAN_FILE)
    if not art or not art.inline_data: return {"status": "no_plan_found"}
    return {"status": "ok", "plan": art.inline_data.data.decode()}

sage = Agent(name="sage", model=MODEL, tools=[save_meal_plan, load_meal_plan],
    instruction="When asked to plan+save meals, pick 3 dishes and call save_meal_plan "
                "(comma-separated). When asked what the saved plan was, call load_meal_plan. Be brief.")
ss = InMemorySessionService(); arts = InMemoryArtifactService()
runner = Runner(agent=sage, app_name="sage", session_service=ss, artifact_service=arts)

print("── Session 1: make + save a plan ──")
await ss.create_session(app_name="sage", user_id="alice", session_id="s1")
await say(runner, "s1", "Plan me 3 quick vegetarian dinners and save it.")
print("── Session 2 (new): re-open the file ──")
await ss.create_session(app_name="sage", user_id="alice", session_id="s2")
await say(runner, "s2", "Remind me — what was my saved meal plan?")
print("✅ The generated plan file persisted and re-loaded in a new session.")
''')

L5 = (r'''
## L5 · Working memory — compaction & rewind 🗜️↩️

The context window is Sage's *short-term* working memory. Two tools keep it healthy:
**compaction** summarizes long chats so they stay affordable, and **rewind** undoes
a turn. (A third, context *caching*, is a transparent cost optimization — nothing
to watch.)
''', r'''
from google.adk.agents import Agent
from google.adk.apps.app import App, EventsCompactionConfig
from google.adk.apps.llm_event_summarizer import LlmEventSummarizer
from google.adk.models import Gemini
from google.adk.runners import InMemoryRunner, Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import ToolContext

print("========== COMPACTION ==========")
chat = Agent(name="sage", model=MODEL, instruction="You are Sage. Answer in ONE short sentence.")
app = App(name="sage", root_agent=chat, events_compaction_config=EventsCompactionConfig(
    compaction_interval=3, overlap_size=1, summarizer=LlmEventSummarizer(llm=Gemini(model=MODEL))))
ss = InMemorySessionService(); runner = Runner(app=app, session_service=ss)
await ss.create_session(app_name="sage", user_id="alice", session_id="s")
for i in range(6):
    async for _ in runner.run_async(user_id="alice", session_id="s",
        new_message=types.Content(role="user", parts=[types.Part(text=f"Quick dinner idea #{i+1}?")])): pass
s = await ss.get_session(app_name="sage", user_id="alice", session_id="s")
comp = [e for e in s.events if getattr(getattr(e,'actions',None),'compaction',None)]
print(f"  {len(s.events)} events; {len(comp)} compaction summary(ies).")
if comp:
    c = comp[0].actions.compaction; content = getattr(c,'compacted_content',c)
    print("  📝", " ".join(p.text for p in content.parts if getattr(p,'text',None))[:180], "…")

print("\\n========== REWIND ==========")
def set_plan(dish: str, tool_context: ToolContext) -> dict:
    """Set tonight's dinner plan."""
    tool_context.state["plan"] = dish; return {"plan": dish}
sage = Agent(name="sage", model=MODEL, tools=[set_plan],
             instruction="When the user names a dinner dish, call set_plan. Be brief.")
r = InMemoryRunner(agent=sage, app_name="sage"); ss2 = r.session_service
await ss2.create_session(app_name="sage", user_id="alice", session_id="s")
async for _ in r.run_async(user_id="alice", session_id="s",
    new_message=types.Content(role="user", parts=[types.Part(text="Plan lentil curry tonight.")])): pass
inv = None
async for ev in r.run_async(user_id="alice", session_id="s",
    new_message=types.Content(role="user", parts=[types.Part(text="Actually, change it to mushroom soup.")])): inv = ev.invocation_id
print("  plan =", (await ss2.get_session(app_name='sage',user_id='alice',session_id='s')).state.get("plan"))
await r.rewind_async(user_id="alice", session_id="s", rewind_before_invocation_id=inv)
print("  after rewind =", (await ss2.get_session(app_name='sage',user_id='alice',session_id='s')).state.get("plan"), " ✅ undone")
''')

L6 = (r'''
## L6 · Surviving time — durability ⏳

Where memory meets long-running work. Sage's grocery order is a
`LongRunningFunctionTool`: it pauses for confirmation, the run **ends**, and it
resumes later when the user confirms. *(Full crash-and-restart story: the
Long-Running Agent lab — github.com/cuppibla/loop-lab-onboarding.)*
''', r'''
from google.adk.agents import Agent
from google.adk.apps.app import App, ResumabilityConfig
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import LongRunningFunctionTool, ToolContext

def order_groceries(items: str, tool_context: ToolContext) -> dict:
    """Place a grocery order. Needs the user to confirm first."""
    return {"status": "pending_confirmation", "items": items}

sage = Agent(name="sage", model=MODEL, tools=[LongRunningFunctionTool(order_groceries)],
    instruction="When asked to order groceries, call order_groceries. After you receive "
                "confirmed=true, say the order is placed. Be brief.")
app = App(name="sage", root_agent=sage, resumability_config=ResumabilityConfig(is_resumable=True))
ss = InMemorySessionService(); runner = Runner(app=app, session_service=ss)
await ss.create_session(app_name="sage", user_id="alice", session_id="s")

async def run(message):
    pend = None
    async for ev in runner.run_async(user_id="alice", session_id="s", new_message=message):
        for f in ev.get_function_calls() or []:
            if ev.long_running_tool_ids and f.id in ev.long_running_tool_ids:
                pend = (f.id, f.name); print(f"       · {f.name} → PENDING (awaiting confirmation)")
        if ev.content and ev.content.parts:
            for p in ev.content.parts:
                if p.text and p.text.strip(): print(f"  🌿 {p.text.strip()}")
    return pend

print("── Sage places an order — it pauses, then the run ends ──")
pend = await run(types.Content(role="user", parts=[types.Part(text="Order groceries: lentils, onions, coconut milk.")]))
print("── Later — the user confirms → the run resumes and completes ──")
fid, fname = pend
await run(types.Content(role="user", parts=[types.Part(
    function_response=types.FunctionResponse(id=fid, name=fname, response={"confirmed": True}))]))
print("✅ A long-running task paused, the run ended, and it resumed later on confirmation.")
''')

L7 = (r'''
## L7 · Managed in the cloud — Vertex sessions + Memory Bank ☁️

The payoff of the whole hierarchy: **the Sage code doesn't change to go to
production — only the services swap.**

```python
# local (L2/L3)                 # managed (L7)
DatabaseSessionService   →  VertexAiSessionService(project, location, agent_engine_id)
InMemoryMemoryService    →  VertexAiMemoryBankService(project, location, agent_engine_id)
```

You get managed sessions + Memory Bank with nothing to run or back up. This step
needs a GCP project + an Agent Engine instance; everything above runs with no cloud.
''', r'''
# Wiring only (runs the live version if you've set GOOGLE_CLOUD_PROJECT + AGENT_ENGINE_ID).
import os
project = os.environ.get("GOOGLE_CLOUD_PROJECT"); aeid = os.environ.get("AGENT_ENGINE_ID")
if not (project and aeid):
    print("⏭ Set GOOGLE_GENAI_USE_VERTEXAI=True, GOOGLE_CLOUD_PROJECT, GOOGLE_CLOUD_LOCATION,")
    print("  and AGENT_ENGINE_ID (an Agent Engine instance) to run Sage on managed services.")
else:
    from google.adk.sessions import VertexAiSessionService
    from google.adk.memory import VertexAiMemoryBankService
    from google.adk.runners import Runner
    loc = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
    runner = Runner(agent=build_sage(), app_name="sage",
        session_service=VertexAiSessionService(project=project, location=loc, agent_engine_id=aeid),
        memory_service=VertexAiMemoryBankService(project=project, location=loc, agent_engine_id=aeid))
    await runner.session_service.create_session(app_name="sage", user_id="alice", session_id="s")
    await say(runner, "s", "Hi Sage, I'm vegetarian — remember that.")
    print("✅ Same Sage, now on managed Vertex sessions + Memory Bank.")
''')

RECAP = r'''
## Recap — the Memory Hierarchy

| Rung | Concept | ADK piece |
|---|---|---|
| within a turn | stateless | `Runner` + `InMemorySessionService` |
| within a chat | scratchpad | `session.state` |
| across chats | durable + scoped | `DatabaseSessionService` · `user:`/`app:` |
| long-term | searchable memory | `MemoryService` · `add_session_to_memory` / `search_memory` |
| files | artifacts | `save/load_artifact` |
| working memory | compaction · rewind · caching | `EventsCompactionConfig` · `rewind_async` |
| surviving time | durability | `ResumabilityConfig` · `LongRunningFunctionTool` |
| managed | zero-infra | `VertexAiSessionService` + `VertexAiMemoryBankService` |

**"Persistence is not memory."** Pick the rung your agent actually needs.
'''


def build(title, levels, out):
    cells = [md(title), md(SETUP_MD), code(SETUP),
             md("### 🌿 The shared Sage base (run this once)"), code(SHARED)]
    for name, intro, body in levels:
        c = code(body)
        c["id"] = name            # stable cell id → codelab links via #scrollTo=<name>
        cells += [md(intro), c]
    if levels is L57:
        cells += [md(RECAP)]
    nb = nbf.v4.new_notebook()
    nb.cells = cells
    nb.metadata = {"kernelspec": {"name": "python3", "display_name": "Python 3"},
                   "colab": {"provenance": []}}
    here = os.path.dirname(__file__)
    nbf.write(nb, os.path.join(here, out))
    print(f"wrote {out}  ({len(cells)} cells)")


L04 = [("l0", *L0), ("l1", *L1), ("l2", *L2), ("l3", *L3), ("l4", *L4)]
L57 = [("l5", *L5), ("l6", *L6), ("l7", *L7)]

build("# 🌿 Sage · Memory Masterclass — Part 1: Remembering\n\n"
      "*How an agent remembers — from a goldfish to long-term memory.*\n\n"
      "Sections: **L0** goldfish · **L1** scratchpad · **L2** across restarts · "
      "**L3** long-term memory · **L4** files. Run the Setup and Sage cells first, "
      "then each section top to bottom.",
      L04, "Sage_memory_1_remembering.ipynb")

build("# 🌿 Sage · Memory Masterclass — Part 2: Managing Memory\n\n"
      "*Keeping memory healthy, durable, and production-ready.*\n\n"
      "Sections: **L5** working memory (compaction/rewind) · **L6** surviving time "
      "(durability) · **L7** managed cloud. Run the Setup and Sage cells first.",
      L57, "Sage_memory_2_managing.ipynb")

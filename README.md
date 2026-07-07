# 🌿 The ADK Memory Masterclass

Give your AI agent a **memory**. This is an advanced, hands-on tour of the whole memory / state /
persistence layer of Google's **Agent Development Kit (ADK)** — taught as one graded climb up
the **Memory Hierarchy**, through a single meal-planning assistant, **Sage**.

> **The one idea:** *"persistence is not memory."* An agent's memory isn't one thing — it's a
> stack of very different mechanisms. This masterclass teaches you which rung to reach for.

## Three ways to take it

- **📖 Codelab (guided):** the step-by-step walkthrough (`CODELAB.md`) — best start-to-finish.
- **▶ Colab (zero setup):** run it in the browser —
  [Part 1 · Remembering](https://colab.research.google.com/drive/1V7I1LHZk_IxcvKkEdTKFkwC35OBNK-cp)
  · [Part 2 · Managing Memory](https://colab.research.google.com/drive/1bJZZz6LKF7Z5OM5eaFZCf4zZMMu795ET)
- **💻 Local:** clone, `./setup_venv.sh` (or `uv sync`), run each level as a module.

## The ladder

Each level answers one question, adds one idea, and runs on its own. The domain is the same
throughout — one assistant, **Sage** — so the rungs accumulate.

| Level | The question | ADK piece | Run it |
|---|---|---|---|
| **[L0](L0_goldfish/)** · goldfish | why is a bare agent forgetful? | `InMemorySessionService` | `python -m L0_goldfish.demo` |
| **[L1](L1_scratchpad/)** · scratchpad | remember within a chat | `session.state` | `python -m L1_scratchpad.demo` |
| **[L2](L2_persistence/)** · across restarts | remember *you*, across sessions | `DatabaseSessionService` · `user:` | `python -m L2_persistence.demo` |
| **[L3](L3_memory/)** · persistence ≠ memory | recall *what happened* | `add_session_to_memory` / `search_memory` | `python -m L3_memory.demo` |
| **[L4](L4_artifacts/)** · files | remember files | `save/load_artifact` | `python -m L4_artifacts.demo` |
| **[L5](L5_context/)** · working memory | long chats, affordably | `EventsCompactionConfig` · `rewind_async` | `python -m L5_context.demo` |
| **[L6](L6_durability/)** · surviving time | pause & resume | `LongRunningFunctionTool` · `ResumabilityConfig` | `python -m L6_durability.demo` |
| **[L7](L7_managed/)** · managed cloud | zero-infra memory | `VertexAiSessionService` · `VertexAiMemoryBankService` | `python -m L7_managed.demo` |

**The through-line:** *forgets everything → remembers this chat → remembers you → knows you →
keeps your files → manages a long memory → survives time → managed.*

## Quickstart (local)

```bash
git clone https://github.com/cuppibla/adk-memory-masterclass.git
cd adk-memory-masterclass
./setup_venv.sh            # Windows: setup_venv.bat   (or: uv sync)
source .venv/bin/activate
# put your Gemini API key in .env  (see .env.example)
python -m L0_goldfish.demo
```

Get a Gemini API key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey).

## Layout

```
shared/        Sage's stable tools + canned recipes (reused by every level)
L0…L7/         one runnable folder per rung (demo.py + README)
notebooks/     the two Colab notebooks + build.py (regenerates them from the code)
reference/     the proof-of-concept scripts that validated the trickier mechanics
CODELAB.md     the guided codelab (claat source)
```

Built and verified on **ADK 2.3.0**. Part of a family of ADK labs — see also
[The Long-Running Agent](https://github.com/cuppibla/loop-lab-onboarding).

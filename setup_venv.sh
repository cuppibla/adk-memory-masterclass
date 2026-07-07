#!/usr/bin/env bash
# One-time local setup (pip flavor). uv users: just run `uv sync`.
set -e
PY=""
for c in python3.13 python3.12 python3.11 python3.10; do command -v "$c" >/dev/null 2>&1 && { PY="$c"; break; }; done
[ -z "$PY" ] && { echo "ERROR: need Python 3.10+ (ADK requirement)." >&2; exit 1; }
echo "Using $($PY --version). Creating .venv…"
"$PY" -m venv .venv && source .venv/bin/activate
pip install --quiet --upgrade pip && pip install --quiet -r requirements.txt
[ -f .env ] || cp .env.example .env
echo "Done. Put your GOOGLE_API_KEY in .env, then: source .venv/bin/activate ; uv run python -m L0_goldfish.demo"

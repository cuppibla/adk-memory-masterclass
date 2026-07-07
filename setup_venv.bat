@echo off
where py >nul 2>nul && (set PY=py -3) || (set PY=python)
%PY% -m venv .venv && call .venv\Scripts\activate
pip install --quiet --upgrade pip && pip install --quiet -r requirements.txt
if not exist .env copy .env.example .env
echo Done. Put your GOOGLE_API_KEY in .env, then activate and run: python -m L0_goldfish.demo

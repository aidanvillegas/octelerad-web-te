# API Service

FastAPI backend for the macro library. Current state includes skeleton database models, placeholder routes, and dependency wiring.

## Local setup

```bash
python -m venv .venv
. .venv/Scripts/Activate.ps1  # or source .venv/bin/activate on mac/linux
pip install -r services/api/requirements.txt
uvicorn app.main:app --reload
```

Endpoints are stubbed and will be implemented during Sprint 1.

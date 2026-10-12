$ErrorActionPreference = "Stop"
python scripts/seed_demo.py
python -m uvicorn app.main:app --reload

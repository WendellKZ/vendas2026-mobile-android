@echo off
cd /d %~dp0
set DATABASE_URL=sqlite:///./erp_vendas_local.db
if not exist .venv (
  python -m venv .venv
)
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 5098
pause

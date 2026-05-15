@echo off
cd /d %~dp0
py -3.12 -m uvicorn app.main:app --host 0.0.0.0 --reload --port 5098
pause

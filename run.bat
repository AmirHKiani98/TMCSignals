@echo off

REM Start backend in a new terminal
start "TMC Backend" cmd /k "call %~dp0.venv\Scripts\activate && cd /d %~dp0backend && python run_daphne.py"

REM Start frontend in a new terminal
start "TMC Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo Both servers starting in separate windows...

@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  call ".venv\Scripts\python.exe" codex_http_demo.py
) else (
  python codex_http_demo.py
)

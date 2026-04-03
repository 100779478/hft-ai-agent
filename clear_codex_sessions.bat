@echo off
setlocal

cd /d "%~dp0"

set "CODEX_DIR=%~dp0.codex"
set "SESSIONS_DIR=%CODEX_DIR%\sessions"
set "ALIASES_FILE=%CODEX_DIR%\session_aliases.json"

echo Target CODEX_HOME: "%CODEX_DIR%"

if exist "%SESSIONS_DIR%" (
  echo Removing sessions directory...
  rmdir /s /q "%SESSIONS_DIR%"
) else (
  echo Sessions directory not found, skipping.
)

if exist "%ALIASES_FILE%" (
  echo Removing session aliases file...
  del /f /q "%ALIASES_FILE%"
) else (
  echo Session aliases file not found, skipping.
)

mkdir "%SESSIONS_DIR%" >nul 2>nul

echo Done. Project Codex sessions have been cleared.
endlocal

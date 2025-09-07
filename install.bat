@echo off
REM Minimal install for marketdata-toolkit (editable mode)

SETLOCAL

REM --- Pick Python 3.11 if available, else fall back to 'python' ---
where py >NUL 2>&1 && (set "PY=py -3.11") || (set "PY=python")

REM --- Create venv if missing ---
IF NOT EXIST .venv (
    %PY% -m venv .venv || (echo Failed to create venv & exit /b 1)
)

REM --- Activate venv ---
call .venv\Scripts\activate || (echo Failed to activate venv & exit /b 1)

REM --- Upgrade basic tooling ---
python -m pip install -U pip setuptools wheel || exit /b 1

REM --- Install this repo in editable mode ---
pip install -e . || exit /b 1

echo.
echo Done. To use later:
echo     call %%~dp0.venv\Scripts\activate
echo Then run:
echo     prices --help
ENDLOCAL

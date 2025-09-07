@echo off
REM Set up a virtual environment and install the marketdata toolkit

SETLOCAL

python --version >NUL 2>&1
IF ERRORLEVEL 1 (
    echo Python is required but was not found in PATH.
    exit /b 1
)

python -m ensurepip --upgrade >NUL 2>&1

IF NOT EXIST .venv (
    python -m venv .venv
)

CALL .venv\Scripts\activate

python -m pip install --upgrade pip wheel
python -m pip install -e .

echo.
echo Installation complete. To activate later run:
echo     call %%~dp0.venv\Scripts\activate
ENDLOCAL

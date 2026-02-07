@echo off
REM Start AI Employee Gold Tier Automation System
REM This script starts the complete workflow orchestrator

echo ============================================================
echo     AI Employee - Starting Gold Tier Automation System
echo ============================================================
echo.

REM Set Python path (adjust if needed)
set PYTHON_PATH=python

REM Set vault path
set VAULT_PATH=C:\Users\LENOVO X1 YOGA\Desktop\hakathone zero\AI_Employee_Vault

echo Starting Workflow Orchestrator...
echo Vault: %VAULT_PATH%
echo.

REM Change to vault directory
cd /d "%VAULT_PATH%"

REM Install required packages if needed
echo Checking dependencies...
%PYTHON_PATH% -c "import schedule" 2>nul
if errorlevel 1 (
    echo Installing schedule library...
    %PYTHON_PATH% -m pip install schedule
)

%PYTHON_PATH% -c "import watchdog" 2>nul
if errorlevel 1 (
    echo Installing watchdog library...
    %PYTHON_PATH% -m pip install watchdog
)

%PYTHON_PATH% -c "import yaml" 2>nul
if errorlevel 1 (
    echo Installing pyyaml library...
    %PYTHON_PATH% -m pip install pyyaml
)

echo.
echo ============================================================
echo All dependencies checked. Starting main system...
echo ============================================================
echo.
echo The system will now:
echo   - Monitor the 'Approved' folder for files to process
echo   - Run periodic tasks (hourly, daily, weekly)
echo   - Check Reddit, Twitter, LinkedIn for opportunities
echo   - Generate content automatically
echo   - Create CEO briefings
echo.
echo Press Ctrl+C to stop the system gracefully.
echo ============================================================
echo.

REM Start the workflow orchestrator
%PYTHON_PATH% workflow_orchestrator.py

echo.
echo ============================================================
echo System stopped.
echo ============================================================
echo.
pause

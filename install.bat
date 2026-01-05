@echo off
REM Egile Agent Hub - Installation Script for Windows
REM ================================================

echo.
echo ========================================
echo Installing Egile Agent Hub
echo ========================================
echo.

REM Install egile-agent-core
echo [1/4] Installing egile-agent-core...
cd ..\egile-agent-core
if errorlevel 1 (
    echo ERROR: Could not find egile-agent-core directory
    echo Make sure it exists at: ..\egile-agent-core
    pause
    exit /b 1
)
pip install -e .
if errorlevel 1 (
    echo ERROR: Failed to install egile-agent-core
    pause
    exit /b 1
)

REM Install egile-mcp-prospectfinder
echo.
echo [2/4] Installing egile-mcp-prospectfinder...
cd ..\egile-mcp-prospectfinder
if errorlevel 1 (
    echo ERROR: Could not find egile-mcp-prospectfinder directory
    echo Make sure it exists at: ..\egile-mcp-prospectfinder
    pause
    exit /b 1
)
pip install -e .
if errorlevel 1 (
    echo ERROR: Failed to install egile-mcp-prospectfinder
    pause
    exit /b 1
)

REM Install egile-agent-prospectfinder
cd ..\egile-agent-prospectfinder
if errorlevel 1 (
    echo WARNING: Could not find egile-agent-prospectfinder directory
    echo Skipping...
) else (
    pip install -e .
)

REM Install egile-mcp-x-post-creator
echo.
echo [3/4] Installing egile-mcp-x-post-creator...
cd ..\egile-mcp-x-post-creator
if errorlevel 1 (
    echo ERROR: Could not find egile-mcp-x-post-creator directory
    echo Make sure it exists at: ..\egile-mcp-x-post-creator
    pause
    exit /b 1
)
pip install -e .
if errorlevel 1 (
    echo ERROR: Failed to install egile-mcp-x-post-creator
    pause
    exit /b 1
)

REM Install egile-agent-x-twitter
cd ..\egile-agent-x-twitter
if errorlevel 1 (
    echo WARNING: Could not find egile-agent-x-twitter directory
    echo Skipping...
) else (
    pip install -e .
)

REM Install egile-agent-hub
echo.
echo [4/4] Installing egile-agent-hub...
cd ..\egile-agent-hub
pip install -e ".[all]"
if errorlevel 1 (
    echo ERROR: Failed to install egile-agent-hub
    pause
    exit /b 1
)

REM Copy .env.example to .env if not exists
if not exist .env (
    echo.
    echo Creating .env file from .env.example...
    copy .env.example .env
    echo.
    echo ========================================
    echo IMPORTANT: Configure your .env file!
    echo ========================================
    echo.
    echo Edit .env and set:
    echo   - At least one AI model API key (MISTRAL_API_KEY, XAI_API_KEY, or OPENAI_API_KEY^)
    echo   - Google API credentials (if using ProspectFinder^)
    echo   - X/Twitter API credentials (if using XTwitter^)
    echo.
)

REM Create empty agents.yaml if not exists
if not exist agents.yaml (
    echo Creating agents.yaml from agents.yaml.example...
    copy agents.yaml.example agents.yaml
    echo.
    echo ========================================
    echo CONFIGURE YOUR AGENTS!
    echo ========================================
    echo.
    echo Edit agents.yaml to define your agents and teams.
    echo See agents.yaml.example for documentation.
    echo.
)

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Next steps:
echo   1. Edit .env with your API keys
echo   2. Edit agents.yaml to define your agents
echo   3. Run: agent-hub
echo.
pause

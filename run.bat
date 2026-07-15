@echo off
setlocal DisableDelayedExpansion
title Kick Installer

cd /d "%~dp0"

:: ANSI colors
for /f "delims=" %%a in ('echo prompt $E ^| cmd') do set "ESC=%%a"

set "CYAN=%ESC%[96m"
set "YELLOW=%ESC%[93m"
set "RED=%ESC%[91m"
set "GREEN=%ESC%[92m"
set "RESET=%ESC%[0m"

cls

echo %CYAN%=========================================%RESET%
echo %YELLOW%        Kick viewbot made by decodehub.org%RESET%
echo %CYAN%=========================================%RESET%
echo.

:: Python check
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo %RED%Python not found.%RESET%
    pause
    exit /b
)

echo %CYAN%Installing packages...%RESET%
python -m pip install websockets tls-client

if %errorlevel% neq 0 (
    echo %RED%Package install failed.%RESET%
    pause
    exit /b
)

echo.
echo %GREEN%Packages installed successfully.%RESET%
echo %CYAN%Starting kick.py...%RESET%
echo.

python kick.py

echo.
echo %YELLOW%Program ended.%RESET%
pause
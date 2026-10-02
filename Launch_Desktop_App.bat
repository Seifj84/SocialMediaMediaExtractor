@echo off
title OmniMedia Desktop App
cd /d "%~dp0"
python app.py
if errorlevel 1 (
    echo.
    echo An error occurred while launching the desktop app.
    pause
)

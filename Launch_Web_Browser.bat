@echo off
title OmniMedia Web App
cd /d "%~dp0"
echo Starting OmniMedia Web UI in your default browser...
python -m streamlit run web.py
pause

"""
OmniMedia Web Application Launcher.
Run `streamlit run web.py` to start the browser UI.
"""

import sys
import subprocess

if __name__ == "__main__":
    from media_extractor.ui.web_streamlit import run_web_app
    run_web_app()

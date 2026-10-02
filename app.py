"""
OmniMedia Desktop Application Launcher.
Run `python app.py` to start the GUI.
"""

import sys
from media_extractor.ui.gui_pyside import launch_gui


def main():
    launch_gui()


if __name__ == "__main__":
    main()

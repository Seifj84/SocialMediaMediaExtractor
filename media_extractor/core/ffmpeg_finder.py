"""
FFmpeg discovery and configuration module.
Locates or configures the FFmpeg binary for high-quality audio extraction and video remuxing.
"""

import os
import shutil
import subprocess
from typing import Optional


_CACHED_FFMPEG_PATH: Optional[str] = None


def find_ffmpeg() -> Optional[str]:
    """
    Finds the absolute path to an available FFmpeg binary.
    Prioritizes:
    1. Explicit FFMPEG_BINARY or FFMPEG_PATH environment variable.
    2. System PATH (e.g., ffmpeg in /usr/bin or Windows PATH).
    3. Bundled binary via `imageio_ffmpeg` library.
    4. Common local program files paths on Windows.
    """
    global _CACHED_FFMPEG_PATH
    if _CACHED_FFMPEG_PATH and os.path.exists(_CACHED_FFMPEG_PATH):
        return _CACHED_FFMPEG_PATH

    # 1. Environment variables
    for env_var in ("FFMPEG_BINARY", "FFMPEG_PATH"):
        path = os.getenv(env_var)
        if path and os.path.exists(path):
            _CACHED_FFMPEG_PATH = os.path.abspath(path)
            return _CACHED_FFMPEG_PATH

    # 2. System PATH
    which_ffmpeg = shutil.which("ffmpeg")
    if which_ffmpeg:
        _CACHED_FFMPEG_PATH = os.path.abspath(which_ffmpeg)
        return _CACHED_FFMPEG_PATH

    # 3. imageio_ffmpeg bundled binary
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.exists(exe):
            _CACHED_FFMPEG_PATH = os.path.abspath(exe)
            return _CACHED_FFMPEG_PATH
    except Exception:
        pass

    # 4. Common Windows directories
    common_locations = [
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        os.path.expanduser(r"~\AppData\Local\Microsoft\WinGet\Links\ffmpeg.exe"),
    ]
    for loc in common_locations:
        if os.path.exists(loc):
            _CACHED_FFMPEG_PATH = os.path.abspath(loc)
            return _CACHED_FFMPEG_PATH

    return None


def ensure_ffmpeg_in_path() -> Optional[str]:
    """
    Ensures the directory containing FFmpeg is in os.environ['PATH'],
    making it accessible to any subprocesses (yt-dlp, gallery-dl).
    """
    ffmpeg_exe = find_ffmpeg()
    if ffmpeg_exe:
        ffmpeg_dir = os.path.dirname(ffmpeg_exe)
        path_env = os.environ.get("PATH", "")
        if ffmpeg_dir.lower() not in path_env.lower():
            os.environ["PATH"] = f"{ffmpeg_dir}{os.pathsep}{path_env}"
        return ffmpeg_exe
    return None


def get_ffmpeg_version(ffmpeg_path: Optional[str] = None) -> Optional[str]:
    """Returns the FFmpeg version string if available."""
    exe = ffmpeg_path or find_ffmpeg()
    if not exe:
        return None
    try:
        result = subprocess.run([exe, "-version"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            first_line = result.stdout.splitlines()[0]
            return first_line.strip()
    except Exception:
        pass
    return None

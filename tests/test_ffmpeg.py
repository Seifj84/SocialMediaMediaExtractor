"""
Tests for FFmpeg detection.
"""

from media_extractor.core.ffmpeg_finder import find_ffmpeg, get_ffmpeg_version


def test_ffmpeg_found():
    ffmpeg = find_ffmpeg()
    assert ffmpeg is not None
    assert "ffmpeg" in ffmpeg.lower()


def test_ffmpeg_version():
    ffmpeg = find_ffmpeg()
    assert ffmpeg is not None
    version = get_ffmpeg_version(ffmpeg)
    assert version is not None
    assert "ffmpeg" in version.lower()

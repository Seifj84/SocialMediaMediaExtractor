"""
Tests for file utility functions.
"""

from media_extractor.utils.file_utils import sanitize_filename, format_bytes


def test_sanitize_filename():
    assert sanitize_filename('invalid:name/with*special?chars"<>|') == "invalid_name_with_special_chars"
    assert sanitize_filename("  spaces and ... dots  ") == "spaces and ... dots"
    assert sanitize_filename("") == "media_item"


def test_format_bytes():
    assert format_bytes(500) == "500.0 B"
    assert format_bytes(2048) == "2.0 KB"
    assert format_bytes(5 * 1024 * 1024) == "5.0 MB"
    assert format_bytes(2 * 1024 * 1024 * 1024) == "2.0 GB"
    assert format_bytes(None) == "Unknown size"

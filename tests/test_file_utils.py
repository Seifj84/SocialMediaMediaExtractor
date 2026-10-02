"""
Tests for file utility functions.
"""

import os
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


def test_extract_activity_name_and_folder():
    from media_extractor.utils.file_utils import extract_activity_name, resolve_activity_folder, write_post_content_txt
    import tempfile

    caption = "Mkutano wa Jukwa la NGOs Mkoa Tanga umeanza leo kwa mafanikio makubwa katika ukumbi wa mkuu wa mkoa."
    act = extract_activity_name(caption)
    assert "Mkutano wa Jukwa la NGOs Mkoa Tanga" in act

    folder = resolve_activity_folder(r"C:\Downloads", caption=caption, date_raw="2026-09-29")
    assert "Mkutano wa Jukwa la NGOs Mkoa Tanga - 2026-09-29" in folder

    with tempfile.TemporaryDirectory() as td:
        txt_path = write_post_content_txt(
            target_dir=td,
            title="Mkutano wa Jukwa la NGOs",
            author="panganidc",
            platform="Instagram",
            url="https://instagram.com/p/123",
            date_str="2026-09-29",
            caption=caption,
            downloaded_files=[]
        )
        assert os.path.exists(txt_path)
        with open(txt_path, "r", encoding="utf-8") as f:
            content = f.read()
            assert "Mkutano wa Jukwa la NGOs" in content
            assert "panganidc" in content

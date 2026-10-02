"""
Tests for configuration management.
"""

import os
from media_extractor.core.config import Config, get_default_download_dir
from media_extractor.core.models import MediaFilter, MediaQuality


def test_default_config():
    cfg = Config()
    assert cfg.default_filter == MediaFilter.ALL
    assert cfg.default_quality == MediaQuality.BEST
    assert cfg.create_author_subfolder is True
    assert cfg.convert_webp_to_jpg is True
    assert "OmniMedia" in cfg.default_output_dir


def test_config_serialization():
    cfg = Config(
        default_output_dir="/custom/path",
        default_filter=MediaFilter.IMAGES_ONLY,
        default_quality=MediaQuality.HIGH,
        create_author_subfolder=False,
    )
    d = cfg.to_dict()
    assert d["default_output_dir"] == "/custom/path"
    assert d["default_filter"] == "images"
    assert d["default_quality"] == "high"
    assert d["create_author_subfolder"] is False

    restored = Config.from_dict(d)
    assert restored.default_output_dir == "/custom/path"
    assert restored.default_filter == MediaFilter.IMAGES_ONLY
    assert restored.default_quality == MediaQuality.HIGH
    assert restored.create_author_subfolder is False

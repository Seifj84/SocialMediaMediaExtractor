"""
Configuration management for OmniMedia Extractor.
Allows customizing default save locations, format conversions, and download preferences.
"""

import json
import os
from dataclasses import dataclass, field, asdict
from typing import Optional
from .models import MediaFilter, MediaQuality


def get_default_download_dir() -> str:
    """Returns the user's default Downloads/OmniMedia folder."""
    user_home = os.path.expanduser("~")
    downloads = os.path.join(user_home, "Downloads", "OmniMedia")
    return downloads


@dataclass
class Config:
    """Application-wide configuration."""
    default_output_dir: str = field(default_factory=get_default_download_dir)
    default_filter: MediaFilter = MediaFilter.ALL
    default_quality: MediaQuality = MediaQuality.BEST
    create_author_subfolder: bool = True
    save_metadata_json: bool = True
    convert_webp_to_jpg: bool = True
    jpg_quality: int = 95
    extract_audio_format: str = "mp3"  # mp3, m4a, wav
    timeout_seconds: int = 30
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )

    def to_dict(self) -> dict:
        data = asdict(self)
        data["default_filter"] = self.default_filter.value
        data["default_quality"] = self.default_quality.value
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        cfg = cls()
        if "default_output_dir" in data:
            cfg.default_output_dir = data["default_output_dir"]
        if "default_filter" in data:
            try:
                cfg.default_filter = MediaFilter(data["default_filter"])
            except ValueError:
                pass
        if "default_quality" in data:
            try:
                cfg.default_quality = MediaQuality(data["default_quality"])
            except ValueError:
                pass
        if "create_author_subfolder" in data:
            cfg.create_author_subfolder = bool(data["create_author_subfolder"])
        if "save_metadata_json" in data:
            cfg.save_metadata_json = bool(data["save_metadata_json"])
        if "convert_webp_to_jpg" in data:
            cfg.convert_webp_to_jpg = bool(data["convert_webp_to_jpg"])
        if "jpg_quality" in data:
            cfg.jpg_quality = int(data["jpg_quality"])
        if "extract_audio_format" in data:
            cfg.extract_audio_format = str(data["extract_audio_format"])
        return cfg


_CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".omni_media", "config.json")


def get_config() -> Config:
    """Loads configuration from persistent disk storage or defaults."""
    if os.path.exists(_CONFIG_PATH):
        try:
            with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return Config.from_dict(data)
        except Exception:
            pass
    return Config()


def save_config(config: Config) -> bool:
    """Saves configuration to persistent disk storage."""
    try:
        os.makedirs(os.path.dirname(_CONFIG_PATH), exist_ok=True)
        with open(_CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config.to_dict(), f, indent=2)
        return True
    except Exception:
        return False

"""
OmniMedia - Universal Social Media Media Extractor
=================================================
A powerful, modular media extraction tool supporting high-resolution photos,
videos, and pristine audio from Instagram, TikTok, YouTube, Twitter/X,
Facebook, Reddit, Pinterest, and 1000+ other platforms.
"""

__version__ = "1.0.0"
__author__ = "Seif Juma"

from .core.models import MediaItem, MediaType, ExtractionResult
from .core.config import Config, get_config
from .extractors.manager import ExtractorManager

__all__ = [
    "MediaItem",
    "MediaType",
    "ExtractionResult",
    "Config",
    "get_config",
    "ExtractorManager",
]

"""
Base Extractor abstract class.
All platform-specific extractors inherit from this base class.
"""

from abc import ABC, abstractmethod
from typing import Optional, Callable
from ..core.models import ExtractionResult, MediaFilter, MediaQuality
from ..core.config import Config, get_config


ProgressCallback = Callable[[int, int, str], None]


class BaseExtractor(ABC):
    """Abstract Base Class for social media extractors."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or get_config()

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Name of the social media platform (e.g., 'Instagram', 'YouTube')."""
        pass

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """Determines if this extractor is suitable for the provided URL."""
        pass

    @abstractmethod
    def extract(
        self,
        url: str,
        output_dir: str,
        media_filter: MediaFilter = MediaFilter.ALL,
        quality: MediaQuality = MediaQuality.BEST,
        progress_cb: Optional[ProgressCallback] = None,
    ) -> ExtractionResult:
        """
        Extracts media from the given URL and saves it to output_dir.
        Returns an ExtractionResult detailing downloaded assets.
        """
        pass

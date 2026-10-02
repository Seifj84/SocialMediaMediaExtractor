"""
Extractor Manager and Registry.
Matches social media URLs to the appropriate dedicated extractor and coordinates extraction.
"""

import time
from typing import List, Optional, Callable
from .base import BaseExtractor, ProgressCallback
from .instagram import InstagramExtractor
from .tiktok import TikTokExtractor
from .youtube import YouTubeExtractor
from .twitter import TwitterExtractor
from .facebook import FacebookExtractor
from .reddit import RedditExtractor
from .pinterest import PinterestExtractor
from .generic import GenericExtractor
from ..core.models import ExtractionResult, MediaFilter, MediaQuality
from ..core.config import Config, get_config
from ..utils.logger import log_info, log_error, log_warning


class ExtractorManager:
    """Coordinates all platform extractors and routes URLs."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or get_config()
        self.extractors: List[BaseExtractor] = [
            InstagramExtractor(self.config),
            TikTokExtractor(self.config),
            YouTubeExtractor(self.config),
            TwitterExtractor(self.config),
            FacebookExtractor(self.config),
            RedditExtractor(self.config),
            PinterestExtractor(self.config),
            GenericExtractor(self.config),  # Universal catch-all fallback
        ]

    def get_extractor(self, url: str) -> BaseExtractor:
        """Finds the first extractor capable of handling the URL."""
        clean_url = url.strip()
        for extractor in self.extractors:
            if extractor.can_handle(clean_url):
                return extractor
        return self.extractors[-1]  # Return GenericExtractor

    def extract(
        self,
        url: str,
        output_dir: Optional[str] = None,
        media_filter: MediaFilter = MediaFilter.ALL,
        quality: MediaQuality = MediaQuality.BEST,
        progress_cb: Optional[ProgressCallback] = None,
    ) -> ExtractionResult:
        """
        Coordinates full extraction workflow:
        1. Selects destination directory (user-provided or config default)
        2. Detects matching extractor
        3. Executes download and format conversion
        4. Writes metadata summary
        """
        clean_url = url.strip()
        destination = output_dir or self.config.default_output_dir
        start_time = time.time()

        extractor = self.get_extractor(clean_url)
        log_info(f"Routed URL to extractor: [bold]{extractor.platform_name}[/bold]")

        from ..core.history import get_history_tracker
        tracker = get_history_tracker()

        try:
            result = extractor.extract(
                url=clean_url,
                output_dir=destination,
                media_filter=media_filter,
                quality=quality,
                progress_cb=progress_cb,
            )
            duration = time.time() - start_time
            tracker.record(result, media_filter=media_filter, quality=quality, duration_seconds=duration)
            return result
        except Exception as e:
            log_error(f"Extraction failed: {e}")
            duration = time.time() - start_time
            failed_res = ExtractionResult(
                platform=extractor.platform_name,
                source_url=clean_url,
                target_dir=destination,
                success=False,
                error_message=str(e),
            )
            tracker.record(failed_res, media_filter=media_filter, quality=quality, duration_seconds=duration)
            return failed_res

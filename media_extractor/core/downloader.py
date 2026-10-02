"""
Core downloader module: multi-stream direct downloading, progress monitoring,
image conversions, and metadata writing.
"""

import json
import os
import time
from typing import Callable, Optional, List
import requests

from .models import MediaItem, MediaType, ExtractionResult, MediaFilter
from .config import Config, get_config
from ..utils.file_utils import sanitize_filename, convert_image_to_jpg, ensure_unique_filepath
from ..utils.logger import log_info, log_success, log_warning, log_error, log_progress


ProgressCallback = Callable[[int, int, str], None]


class Downloader:
    """Handles downloading media items to the specified destination directory."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or get_config()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.config.user_agent,
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
        })

    def download_direct_item(
        self,
        item: MediaItem,
        target_dir: str,
        prefix: str = "",
        progress_cb: Optional[ProgressCallback] = None
    ) -> List[str]:
        """
        Downloads a single MediaItem with a direct URL.
        Returns a list of saved file paths (e.g. original + converted JPG).
        """
        if not item.url:
            return []

        saved_files = []
        os.makedirs(target_dir, exist_ok=True)

        ext = (item.extension or "bin").lstrip(".").lower()
        base_name = sanitize_filename(f"{prefix}_{item.id}" if prefix else item.id)

        original_filename = f"{base_name}.{ext}"
        original_path = os.path.join(target_dir, original_filename)
        original_path = ensure_unique_filepath(original_path)

        # Download with stream
        try:
            resp = self.session.get(item.url, stream=True, timeout=self.config.timeout_seconds)
            resp.raise_for_status()

            raw_bytes = bytearray()
            with open(original_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)
                        raw_bytes.extend(chunk)

            item.local_filepath = original_path
            item.local_filename = os.path.basename(original_path)
            item.filesize_bytes = os.path.getsize(original_path)
            saved_files.append(original_path)

            # If image is webp and conversion is enabled, save companion JPG
            if ext == "webp" and self.config.convert_webp_to_jpg and item.media_type in (MediaType.IMAGE, MediaType.UNKNOWN):
                jpg_filename = f"{base_name}.jpg"
                jpg_path = os.path.join(target_dir, jpg_filename)
                jpg_path = ensure_unique_filepath(jpg_path)
                converted = convert_image_to_jpg(bytes(raw_bytes), jpg_path, quality=self.config.jpg_quality)
                if converted:
                    saved_files.append(converted)

        except Exception as e:
            log_error(f"Failed to download {item.url}: {e}")

        return saved_files

    def save_result_metadata(self, result: ExtractionResult, target_dir: str) -> str:
        """Writes comprehensive JSON metadata to target_dir/metadata.json."""
        os.makedirs(target_dir, exist_ok=True)
        meta_path = os.path.join(target_dir, "metadata.json")
        try:
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
            result.metadata_file = meta_path
        except Exception as e:
            log_warning(f"Could not save metadata.json: {e}")
        return meta_path

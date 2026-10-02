"""
Twitter / X Media Extractor.
Extracts pristine images, galleries, GIFs, and videos from X/Twitter posts.
"""

import json
import os
import re
from typing import Optional, List
import yt_dlp

from .base import BaseExtractor, ProgressCallback
from ..core.models import ExtractionResult, MediaItem, MediaType, MediaFilter, MediaQuality
from ..core.ffmpeg_finder import ensure_ffmpeg_in_path, find_ffmpeg
from ..utils.file_utils import sanitize_filename
from ..utils.logger import log_info, log_success, log_warning, log_error


class TwitterExtractor(BaseExtractor):
    """Extractor for Twitter and X posts."""

    @property
    def platform_name(self) -> str:
        return "Twitter/X"

    def can_handle(self, url: str) -> bool:
        patterns = [
            r'(?:twitter|x)\.com/\w+/status/\d+',
        ]
        return any(re.search(p, url, re.I) for p in patterns)

    def extract(
        self,
        url: str,
        output_dir: str,
        media_filter: MediaFilter = MediaFilter.ALL,
        quality: MediaQuality = MediaQuality.BEST,
        progress_cb: Optional[ProgressCallback] = None,
    ) -> ExtractionResult:
        log_info(f"Extracting Twitter/X media from: {url}")
        ensure_ffmpeg_in_path()
        ffmpeg_exe = find_ffmpeg()

        # Normalize x.com to twitter.com for maximum extractor compatibility
        clean_url = re.sub(r'https?://x\.com/', 'https://twitter.com/', url, flags=re.I)

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
        }
        if ffmpeg_exe:
            ydl_opts["ffmpeg_location"] = os.path.dirname(ffmpeg_exe)

        if media_filter == MediaFilter.AUDIO_ONLY:
            ydl_opts["format"] = "bestaudio/best"
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": self.config.extract_audio_format,
                "preferredquality": "320",
            }]
        else:
            ydl_opts["format"] = "best"

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(clean_url, download=False)
            uploader = sanitize_filename(info.get("uploader") or info.get("uploader_id") or "x_user")
            post_id = info.get("id") or "post"

            if self.config.create_author_subfolder:
                target_dir = os.path.join(output_dir, uploader)
            else:
                target_dir = output_dir
            os.makedirs(target_dir, exist_ok=True)

            ydl_opts["outtmpl"] = os.path.join(target_dir, f"{uploader}_{post_id}_%(id)s.%(ext)s")

        downloaded_files: List[str] = []
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            download_info = ydl.extract_info(clean_url, download=True)
            if "_filename" in download_info:
                fname = download_info["_filename"]
                if os.path.exists(fname):
                    downloaded_files.append(fname)

            if "requested_downloads" in download_info:
                for req in download_info["requested_downloads"]:
                    path = req.get("filepath") or req.get("_filename")
                    if path and os.path.exists(path) and path not in downloaded_files:
                        downloaded_files.append(path)

        result = ExtractionResult(
            platform="Twitter/X",
            source_url=url,
            author=uploader,
            title=info.get("title") or f"Tweet by @{uploader}",
            caption=info.get("description") or "",
            upload_date=info.get("upload_date"),
            target_dir=target_dir,
            downloaded_files=downloaded_files,
            success=True,
        )

        if self.config.save_metadata_json:
            meta_path = os.path.join(target_dir, f"{uploader}_{post_id}_metadata.json")
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
            result.metadata_file = meta_path

        log_success(f"Twitter/X download complete: {len(downloaded_files)} file(s) saved to {target_dir}")
        return result

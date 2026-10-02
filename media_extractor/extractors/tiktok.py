"""
TikTok Extractor.
Extracts watermark-free videos, photo mode slideshows, and audio tracks from TikTok URLs.
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


class TikTokExtractor(BaseExtractor):
    """Extractor for TikTok videos, photo slideshows, and audio."""

    @property
    def platform_name(self) -> str:
        return "TikTok"

    def can_handle(self, url: str) -> bool:
        patterns = [
            r'tiktok\.com/@[\w.-]+/video/\d+',
            r'tiktok\.com/@[\w.-]+/photo/\d+',
            r'vt\.tiktok\.com/[\w.-]+',
            r'vm\.tiktok\.com/[\w.-]+',
            r'tiktok\.com/t/[\w.-]+',
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
        log_info(f"Extracting TikTok media from: {url}")
        ensure_ffmpeg_in_path()
        ffmpeg_exe = find_ffmpeg()

        def ydl_hook(d):
            if d.get("status") == "downloading" and progress_cb:
                total_bytes = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded_bytes = d.get("downloaded_bytes") or 0
                percent = (downloaded_bytes / total_bytes * 100) if total_bytes > 0 else 0
                progress_cb(int(percent), 100, f"Downloading TikTok: {percent:.1f}%")

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [ydl_hook],
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
            info = ydl.extract_info(url, download=False)
            uploader = sanitize_filename(info.get("uploader") or info.get("creator") or "tiktok_user")
            title = sanitize_filename(info.get("title") or info.get("id") or "tiktok_media")

            if self.config.create_author_subfolder:
                target_dir = os.path.join(output_dir, uploader)
            else:
                target_dir = output_dir
            os.makedirs(target_dir, exist_ok=True)

            ydl_opts["outtmpl"] = os.path.join(target_dir, "%(id)s_%(title)s.%(ext)s")

        downloaded_files: List[str] = []
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            download_info = ydl.extract_info(url, download=True)
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
            platform="TikTok",
            source_url=url,
            author=uploader,
            title=info.get("title") or "",
            caption=info.get("description") or "",
            upload_date=info.get("upload_date"),
            target_dir=target_dir,
            downloaded_files=downloaded_files,
            success=True,
        )

        if self.config.save_metadata_json:
            meta_path = os.path.join(target_dir, f"{title}_metadata.json")
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
            result.metadata_file = meta_path

        log_success(f"TikTok download complete: {len(downloaded_files)} file(s) saved to {target_dir}")
        return result

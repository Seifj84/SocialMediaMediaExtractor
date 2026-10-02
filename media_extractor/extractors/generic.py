"""
Generic Universal Media Extractor.
Leverages yt-dlp and gallery-dl to support over 1,000+ social and multimedia websites.
"""

import json
import os
from typing import Optional, List
import yt_dlp

from .base import BaseExtractor, ProgressCallback
from ..core.models import ExtractionResult, MediaItem, MediaType, MediaFilter, MediaQuality
from ..core.ffmpeg_finder import ensure_ffmpeg_in_path, find_ffmpeg
from ..utils.file_utils import (
    sanitize_filename, resolve_activity_folder, extract_activity_name,
    format_post_date, write_post_content_txt
)
from ..utils.logger import log_info, log_success, log_warning, log_error


class GenericExtractor(BaseExtractor):
    """Universal fallback extractor supporting 1,000+ sites."""

    @property
    def platform_name(self) -> str:
        return "Universal"

    def can_handle(self, url: str) -> bool:
        # Handles any valid HTTP / HTTPS URL
        return url.startswith("http://") or url.startswith("https://")

    def extract(
        self,
        url: str,
        output_dir: str,
        media_filter: MediaFilter = MediaFilter.ALL,
        quality: MediaQuality = MediaQuality.BEST,
        progress_cb: Optional[ProgressCallback] = None,
    ) -> ExtractionResult:
        log_info(f"Extracting media using Universal Extractor from: {url}")
        ensure_ffmpeg_in_path()
        ffmpeg_exe = find_ffmpeg()

        def ydl_hook(d):
            if d.get("status") == "downloading" and progress_cb:
                total_bytes = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded_bytes = d.get("downloaded_bytes") or 0
                percent = (downloaded_bytes / total_bytes * 100) if total_bytes > 0 else 0
                progress_cb(int(percent), 100, f"Downloading: {percent:.1f}%")

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
            ydl_opts["format"] = "bestvideo+bestaudio/best"

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
            except Exception as e:
                # If video extraction fails, try standard format
                ydl_opts["format"] = "best"
                with yt_dlp.YoutubeDL(ydl_opts) as ydl2:
                    info = ydl2.extract_info(url, download=False)

            extractor_name = info.get("extractor") or "Generic"
            uploader = sanitize_filename(info.get("uploader") or info.get("channel") or "media")
            raw_title = info.get("title") or info.get("id") or "download"
            raw_desc = info.get("description") or ""
            upload_date = info.get("upload_date")
            date_str = format_post_date(upload_date)
            activity_name = extract_activity_name(caption=raw_desc, title=raw_title, fallback=uploader)

            if self.config.organize_by_activity:
                target_dir = resolve_activity_folder(
                    base_output_dir=output_dir,
                    caption=raw_desc,
                    title=activity_name,
                    fallback_author=uploader,
                    date_raw=upload_date,
                    custom_folder_name=getattr(self.config, 'custom_folder_name', None)
                )
            elif self.config.create_author_subfolder:
                target_dir = os.path.join(output_dir, extractor_name, uploader)
            else:
                target_dir = output_dir
            os.makedirs(target_dir, exist_ok=True)

            ydl_opts["outtmpl"] = os.path.join(target_dir, "%(title)s_%(id)s.%(ext)s")

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

        # Write post_content.txt
        txt_path = None
        if self.config.save_post_content_txt and downloaded_files:
            txt_path = write_post_content_txt(
                target_dir=target_dir,
                title=activity_name,
                author=uploader,
                platform=extractor_name,
                url=url,
                date_str=date_str,
                caption=raw_desc,
                downloaded_files=downloaded_files
            )
            downloaded_files.append(txt_path)

        result = ExtractionResult(
            platform=extractor_name,
            source_url=url,
            author=uploader,
            title=raw_title,
            activity_name=activity_name,
            caption=raw_desc,
            upload_date=date_str,
            target_dir=target_dir,
            downloaded_files=downloaded_files,
            post_content_file=txt_path,
            success=len(downloaded_files) > 0,
        )

        if self.config.save_metadata_json and downloaded_files:
            meta_path = os.path.join(target_dir, f"{sanitize_filename(raw_title)}_metadata.json")
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
            result.metadata_file = meta_path

        log_success(f"Universal download complete: {len(downloaded_files)} file(s) saved to {target_dir}")
        return result

"""
Pinterest Media Extractor.
Extracts high-resolution original images, animations, and video pins from Pinterest.
"""

import json
import os
import re
from typing import Optional, List
import requests
from bs4 import BeautifulSoup
import yt_dlp

from .base import BaseExtractor, ProgressCallback
from ..core.models import ExtractionResult, MediaItem, MediaType, MediaFilter, MediaQuality
from ..core.ffmpeg_finder import ensure_ffmpeg_in_path, find_ffmpeg
from ..utils.file_utils import (
    sanitize_filename, ensure_unique_filepath,
    resolve_activity_folder, extract_activity_name,
    format_post_date, write_post_content_txt
)
from ..utils.logger import log_info, log_success, log_warning, log_error


class PinterestExtractor(BaseExtractor):
    """Extractor for Pinterest pins (images and videos)."""

    @property
    def platform_name(self) -> str:
        return "Pinterest"

    def can_handle(self, url: str) -> bool:
        patterns = [
            r'pinterest\.(?:com|[a-z]{2})/pin/\d+',
            r'pin\.it/[A-Za-z0-9]+',
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
        log_info(f"Extracting Pinterest media from: {url}")
        headers = {"User-Agent": self.config.user_agent}

        # Follow redirects for short links (e.g. pin.it)
        session = requests.Session()
        session.headers.update(headers)
        r = session.get(url, allow_redirects=True, timeout=15)
        final_url = r.url

        # Check for Pinterest video first via yt-dlp
        downloaded_files: List[str] = []
        author = "pinterest_user"
        pin_id = "pin"
        pin_id_match = re.search(r'/pin/(\d+)', final_url)
        if pin_id_match:
            pin_id = pin_id_match.group(1)

        # Attempt high-res image extraction from HTML
        soup = BeautifulSoup(r.text, "html.parser")
        raw_title = soup.title.string.strip() if (soup.title and soup.title.string) else f"Pinterest_Pin_{pin_id}"
        date_str = format_post_date()
        activity_name = extract_activity_name(title=raw_title, fallback=f"Pinterest_Pin_{pin_id}")

        if self.config.organize_by_activity:
            target_dir = resolve_activity_folder(
                base_output_dir=output_dir,
                title=activity_name,
                fallback_author="Pinterest",
                date_raw=date_str,
                custom_folder_name=getattr(self.config, 'custom_folder_name', None)
            )
        elif self.config.create_author_subfolder:
            target_dir = os.path.join(output_dir, "Pinterest")
        else:
            target_dir = output_dir
        os.makedirs(target_dir, exist_ok=True)

        # Search for original images in og:image or pin metadata
        images_found = set()
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            content = og_image["content"]
            # Convert /x/ or /736x/ to /originals/ for maximum resolution
            orig_url = re.sub(r'/[0-9]+x/', '/originals/', content)
            images_found.add(orig_url)

        # Look in page source for i.pinimg.com/originals
        for m in re.finditer(r'https?://i\.pinimg\.com/originals/[a-zA-Z0-9/_.-]+', r.text):
            images_found.add(m.group(0))

        if images_found and media_filter != MediaFilter.VIDEOS_ONLY:
            for idx, img_url in enumerate(images_found, start=1):
                try:
                    ext = img_url.split(".")[-1].split("?")[0]
                    save_path = os.path.join(target_dir, f"{pin_id}_{idx:02d}.{ext}")
                    save_path = ensure_unique_filepath(save_path)
                    img_resp = session.get(img_url, timeout=20)
                    if img_resp.status_code == 200:
                        with open(save_path, "wb") as f:
                            f.write(img_resp.content)
                        downloaded_files.append(save_path)
                except Exception as e:
                    log_warning(f"Failed to download image {img_url}: {e}")

        # If no image found or videos requested, run yt-dlp
        if not downloaded_files or media_filter in (MediaFilter.VIDEOS_ONLY, MediaFilter.AUDIO_ONLY):
            ensure_ffmpeg_in_path()
            ffmpeg_exe = find_ffmpeg()
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "outtmpl": os.path.join(target_dir, f"{pin_id}_%(title)s.%(ext)s"),
            }
            if ffmpeg_exe:
                ydl_opts["ffmpeg_location"] = os.path.dirname(ffmpeg_exe)
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(final_url, download=True)
                    if "_filename" in info and os.path.exists(info["_filename"]):
                        downloaded_files.append(info["_filename"])
            except Exception:
                pass

        # Write post_content.txt
        txt_path = None
        if self.config.save_post_content_txt and downloaded_files:
            txt_path = write_post_content_txt(
                target_dir=target_dir,
                title=activity_name,
                author=author,
                platform="Pinterest",
                url=url,
                date_str=date_str,
                caption=raw_title,
                downloaded_files=downloaded_files
            )
            downloaded_files.append(txt_path)

        result = ExtractionResult(
            platform="Pinterest",
            source_url=url,
            author=author,
            title=raw_title,
            activity_name=activity_name,
            upload_date=date_str,
            target_dir=target_dir,
            downloaded_files=downloaded_files,
            post_content_file=txt_path,
            success=len(downloaded_files) > 0,
        )

        if self.config.save_metadata_json and downloaded_files:
            meta_path = os.path.join(target_dir, f"{pin_id}_metadata.json")
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
            result.metadata_file = meta_path

        log_success(f"Pinterest download complete: {len(downloaded_files)} file(s) saved to {target_dir}")
        return result

"""
Reddit Media Extractor.
Extracts high-resolution images, multi-image galleries, and v.redd.it videos (with audio merged).
"""

import json
import os
import re
from typing import Optional, List
import yt_dlp
import requests

from .base import BaseExtractor, ProgressCallback
from ..core.models import ExtractionResult, MediaItem, MediaType, MediaFilter, MediaQuality
from ..core.ffmpeg_finder import ensure_ffmpeg_in_path, find_ffmpeg
from ..utils.file_utils import (
    sanitize_filename, ensure_unique_filepath,
    resolve_activity_folder, extract_activity_name,
    format_post_date, write_post_content_txt
)
from ..utils.logger import log_info, log_success, log_warning, log_error


class RedditExtractor(BaseExtractor):
    """Extractor for Reddit submissions, galleries, and videos."""

    @property
    def platform_name(self) -> str:
        return "Reddit"

    def can_handle(self, url: str) -> bool:
        patterns = [
            r'reddit\.com/r/\w+/comments/\w+',
            r'redd\.it/\w+',
            r'v\.redd\.it/\w+',
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
        log_info(f"Extracting Reddit media from: {url}")
        ensure_ffmpeg_in_path()
        ffmpeg_exe = find_ffmpeg()

        # Try JSON API first for Reddit image galleries and pristine uncompressed images
        clean_url = url.split("?")[0].rstrip("/")
        json_url = f"{clean_url}.json"

        headers = {"User-Agent": self.config.user_agent}
        downloaded_files: List[str] = []

        try:
            r = requests.get(json_url, headers=headers, timeout=15)
            if r.status_code == 200:
                data = r.json()
                post = data[0]["data"]["children"][0]["data"]
                author = sanitize_filename(post.get("author") or "reddit_user")
                raw_title = post.get("title") or "Reddit_Post"
                raw_desc = post.get("selftext") or ""
                created_utc = post.get("created_utc")
                date_str = format_post_date(created_utc)
                activity_name = extract_activity_name(caption=raw_desc, title=raw_title, fallback=author)
                subreddit = post.get("subreddit") or ""

                if self.config.organize_by_activity:
                    target_dir = resolve_activity_folder(
                        base_output_dir=output_dir,
                        caption=raw_desc,
                        title=activity_name,
                        fallback_author=author,
                        date_raw=created_utc,
                        custom_folder_name=getattr(self.config, 'custom_folder_name', None)
                    )
                elif self.config.create_author_subfolder:
                    target_dir = os.path.join(output_dir, f"r_{subreddit}_{author}")
                else:
                    target_dir = output_dir
                os.makedirs(target_dir, exist_ok=True)

                # Check gallery data
                if "media_metadata" in post and post.get("is_gallery"):
                    log_info("Detected Reddit image gallery...")
                    media_meta = post["media_metadata"]
                    for idx, (media_id, item_info) in enumerate(media_meta.items(), start=1):
                        if item_info.get("status") != "valid":
                            continue
                        ext = item_info.get("m", "image/jpg").split("/")[-1]
                        s = item_info.get("s", {})
                        img_url = s.get("u") or s.get("gif")
                        if not img_url:
                            continue
                        img_url = img_url.replace("&amp;", "&")

                        img_resp = requests.get(img_url, headers=headers, timeout=20)
                        if img_resp.status_code == 200:
                            save_path = os.path.join(target_dir, f"{author}_{idx:02d}.{ext}")
                            save_path = ensure_unique_filepath(save_path)
                            with open(save_path, "wb") as f:
                                f.write(img_resp.content)
                            downloaded_files.append(save_path)

                    if downloaded_files:
                        # Write post_content.txt
                        txt_path = None
                        if self.config.save_post_content_txt:
                            txt_path = write_post_content_txt(
                                target_dir=target_dir,
                                title=activity_name,
                                author=author,
                                platform="Reddit",
                                url=url,
                                date_str=date_str,
                                caption=raw_desc,
                                downloaded_files=downloaded_files
                            )
                            downloaded_files.append(txt_path)

                        res = ExtractionResult(
                            platform="Reddit",
                            source_url=url,
                            author=author,
                            title=raw_title,
                            activity_name=activity_name,
                            caption=raw_desc,
                            upload_date=date_str,
                            target_dir=target_dir,
                            downloaded_files=downloaded_files,
                            post_content_file=txt_path,
                            success=True
                        )
                        if self.config.save_metadata_json:
                            meta_path = os.path.join(target_dir, "metadata.json")
                            with open(meta_path, "w", encoding="utf-8") as f:
                                json.dump(res.to_dict(), f, indent=2, ensure_ascii=False)
                            res.metadata_file = meta_path
                        return res
        except Exception:
            pass

        # Fallback to yt-dlp for Reddit video or single posts
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
        }
        if ffmpeg_exe:
            ydl_opts["ffmpeg_location"] = os.path.dirname(ffmpeg_exe)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            uploader = sanitize_filename(info.get("uploader") or "reddit_user")
            title = sanitize_filename(info.get("title") or "Reddit_Media")

            if self.config.create_author_subfolder:
                target_dir = os.path.join(output_dir, uploader)
            else:
                target_dir = output_dir
            os.makedirs(target_dir, exist_ok=True)

            ydl_opts["outtmpl"] = os.path.join(target_dir, "%(title)s_%(id)s.%(ext)s")

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
            platform="Reddit",
            source_url=url,
            author=uploader,
            title=title,
            caption=info.get("description") or "",
            target_dir=target_dir,
            downloaded_files=downloaded_files,
            success=True,
        )
        return result

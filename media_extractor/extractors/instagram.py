"""
Instagram Extractor.
Extracts high-resolution images, carousels, reels, and videos from Instagram posts.
Uses embed GraphQL metadata parsing with automatic fallback to yt-dlp / gallery-dl.
"""

import json
import os
import re
import time
from typing import Optional, List
import requests
from PIL import Image
import io

from .base import BaseExtractor, ProgressCallback
from ..core.models import ExtractionResult, MediaItem, MediaType, MediaFilter, MediaQuality
from ..core.ffmpeg_finder import ensure_ffmpeg_in_path, find_ffmpeg
from ..utils.file_utils import sanitize_filename, convert_image_to_jpg, ensure_unique_filepath
from ..utils.logger import log_info, log_success, log_warning, log_error, log_progress


class InstagramExtractor(BaseExtractor):
    """Extractor for Instagram posts, carousels, and reels."""

    @property
    def platform_name(self) -> str:
        return "Instagram"

    def can_handle(self, url: str) -> bool:
        return bool(re.search(r'instagram\.com/(?:p|reel|tv|stories)/[A-Za-z0-9_-]+', url, re.I))

    def extract_shortcode(self, url: str) -> str:
        patterns = [
            r'instagram\.com/(?:p|reel|tv)/([A-Za-z0-9_-]+)',
            r'/p/([A-Za-z0-9_-]+)',
            r'/reel/([A-Za-z0-9_-]+)',
            r'/tv/([A-Za-z0-9_-]+)',
        ]
        for p in patterns:
            m = re.search(p, url)
            if m:
                return m.group(1)
        raise ValueError(f"Could not extract Instagram shortcode from URL: {url}")

    def extract(
        self,
        url: str,
        output_dir: str,
        media_filter: MediaFilter = MediaFilter.ALL,
        quality: MediaQuality = MediaQuality.BEST,
        progress_cb: Optional[ProgressCallback] = None,
    ) -> ExtractionResult:
        shortcode = self.extract_shortcode(url)
        log_info(f"Processing Instagram shortcode: {shortcode}")

        # Attempt Method 1: Embed GraphQL parsing (fastest & highest resolution original images)
        try:
            return self._extract_via_embed_graphql(url, shortcode, output_dir, media_filter, progress_cb)
        except Exception as e:
            log_warning(f"Direct Instagram embed extraction failed ({e}). Falling back to yt-dlp/gallery-dl...")
            return self._extract_via_fallback(url, output_dir, media_filter, progress_cb)

    def _extract_via_embed_graphql(
        self,
        url: str,
        shortcode: str,
        output_dir: str,
        media_filter: MediaFilter,
        progress_cb: Optional[ProgressCallback]
    ) -> ExtractionResult:
        embed_url = f"https://www.instagram.com/p/{shortcode}/embed/captioned/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1"
        }

        session = requests.Session()
        session.headers.update(headers)
        resp = session.get(embed_url, timeout=self.config.timeout_seconds)
        resp.raise_for_status()

        m = re.search(r'"contextJSON"\s*:\s*"({.+?})"\s*[,}\]]', resp.text)
        if not m:
            raise RuntimeError("Embed contextJSON not found in response HTML")

        clean_json_str = json.loads(f'"{m.group(1)}"')
        data = json.loads(clean_json_str)

        gql = data.get("gql_data", {}).get("shortcode_media", {})
        if not gql:
            raise RuntimeError("Missing shortcode_media in parsed Instagram data")

        owner = gql.get("owner", {})
        username = owner.get("username") or "instagram_user"
        full_name = owner.get("full_name") or ""
        caption_edges = gql.get("edge_media_to_caption", {}).get("edges", [])
        caption = caption_edges[0]["node"]["text"] if caption_edges else ""

        # Determine target directory
        if self.config.create_author_subfolder:
            target_dir = os.path.join(output_dir, sanitize_filename(username))
        else:
            target_dir = output_dir
        os.makedirs(target_dir, exist_ok=True)

        items_nodes = []
        edges = gql.get("edge_sidecar_to_children", {}).get("edges", [])
        if edges:
            for edge in edges:
                items_nodes.append(edge["node"])
        else:
            items_nodes.append(gql)

        result = ExtractionResult(
            platform="Instagram",
            source_url=url,
            author=username,
            author_id=owner.get("id"),
            title=f"Instagram post by @{username}",
            caption=caption,
            target_dir=target_dir,
            success=True,
        )

        total = len(items_nodes)
        session = requests.Session()
        session.headers.update(headers)

        for idx, node in enumerate(items_nodes, start=1):
            is_video = node.get("is_video", False)
            if is_video and media_filter == MediaFilter.IMAGES_ONLY:
                continue
            if not is_video and media_filter in (MediaFilter.VIDEOS_ONLY, MediaFilter.AUDIO_ONLY):
                continue

            if progress_cb:
                progress_cb(idx, total, f"Downloading item {idx}/{total}")

            if is_video:
                video_url = node.get("video_url")
                if video_url:
                    video_name = sanitize_filename(f"{username}_{shortcode}_{idx:02d}.mp4")
                    video_path = os.path.join(target_dir, video_name)
                    video_path = ensure_unique_filepath(video_path)
                    v_resp = session.get(video_url, stream=True, timeout=30)
                    v_resp.raise_for_status()
                    with open(video_path, "wb") as f:
                        for chunk in v_resp.iter_content(chunk_size=65536):
                            if chunk:
                                f.write(chunk)
                    result.downloaded_files.append(video_path)
                    item = MediaItem(
                        id=f"{shortcode}_{idx}",
                        media_type=MediaType.VIDEO,
                        url=video_url,
                        local_filename=os.path.basename(video_path),
                        local_filepath=video_path,
                        filesize_bytes=os.path.getsize(video_path)
                    )
                    result.media_items.append(item)
                    continue

            # Process Image
            resources = node.get("display_resources", [])
            if resources:
                best_res = max(resources, key=lambda r: r.get("config_width", 0) * r.get("config_height", 0))
                best_url = best_res.get("src")
                width = best_res.get("config_width")
                height = best_res.get("config_height")
            else:
                best_url = node.get("display_url")
                dim = node.get("dimensions", {})
                width = dim.get("width")
                height = dim.get("height")

            if not best_url:
                continue
            best_url = best_url.replace(r"\/", "/")

            img_resp = session.get(best_url, timeout=30)
            img_resp.raise_for_status()

            # Save pristine original file to webp subfolder
            webp_dir = os.path.join(target_dir, "webp")
            os.makedirs(webp_dir, exist_ok=True)
            webp_name = sanitize_filename(f"{username}_{shortcode}_{idx:02d}.webp")
            webp_path = os.path.join(webp_dir, webp_name)
            webp_path = ensure_unique_filepath(webp_path)
            with open(webp_path, "wb") as f:
                f.write(img_resp.content)
            result.downloaded_files.append(webp_path)

            # Companion high-quality JPG in main directory
            jpg_name = sanitize_filename(f"{username}_{shortcode}_{idx:02d}.jpg")
            jpg_path = os.path.join(target_dir, jpg_name)
            jpg_path = ensure_unique_filepath(jpg_path)
            if self.config.convert_webp_to_jpg:
                converted = convert_image_to_jpg(img_resp.content, jpg_path, quality=self.config.jpg_quality)
                if converted:
                    result.downloaded_files.append(converted)

            item = MediaItem(
                id=f"{shortcode}_{idx}",
                media_type=MediaType.IMAGE,
                url=best_url,
                width=width,
                height=height,
                local_filename=os.path.basename(jpg_path if os.path.exists(jpg_path) else webp_path),
                local_filepath=jpg_path if os.path.exists(jpg_path) else webp_path,
                filesize_bytes=os.path.getsize(webp_path),
            )
            result.media_items.append(item)
            time.sleep(0.15)

        # Write metadata.json
        if self.config.save_metadata_json:
            meta_path = os.path.join(target_dir, "metadata.json")
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
            result.metadata_file = meta_path

        log_success(f"Instagram extraction complete: {len(result.downloaded_files)} files saved to {target_dir}")
        return result

    def _extract_via_fallback(
        self,
        url: str,
        output_dir: str,
        media_filter: MediaFilter,
        progress_cb: Optional[ProgressCallback]
    ) -> ExtractionResult:
        """Fallback to yt-dlp if GraphQL embed fails."""
        import yt_dlp
        ensure_ffmpeg_in_path()
        ffmpeg_exe = find_ffmpeg()

        ydl_opts = {
            "outtmpl": os.path.join(output_dir, "%(uploader,creator,channel,title)s", "%(id)s.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
        }
        if ffmpeg_exe:
            ydl_opts["ffmpeg_location"] = os.path.dirname(ffmpeg_exe)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            saved_dir = output_dir
            downloaded = []
            if "_filename" in info:
                downloaded.append(info["_filename"])

            result = ExtractionResult(
                platform="Instagram",
                source_url=url,
                author=info.get("uploader") or "instagram_user",
                title=info.get("title") or "Instagram Media",
                caption=info.get("description") or "",
                target_dir=saved_dir,
                downloaded_files=downloaded,
                success=True,
            )
            return result

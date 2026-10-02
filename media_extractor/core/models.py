"""
Data models and enumerations for the OmniMedia extractor.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any


class MediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    CAROUSEL = "carousel"
    UNKNOWN = "unknown"


class MediaFilter(str, Enum):
    ALL = "all"
    IMAGES_ONLY = "images"
    VIDEOS_ONLY = "videos"
    AUDIO_ONLY = "audio"


class MediaQuality(str, Enum):
    BEST = "best"
    HIGH = "high"       # 1080p / high bitrate
    MEDIUM = "medium"   # 720p
    AUDIO_320K = "320k" # High quality audio


@dataclass
class MediaItem:
    """Represents an individual media asset to download or that has been downloaded."""
    id: str
    media_type: MediaType
    url: Optional[str] = None
    title: str = ""
    extension: str = ""
    width: Optional[int] = None
    height: Optional[int] = None
    filesize_bytes: Optional[int] = None
    duration_seconds: Optional[float] = None
    thumbnail_url: Optional[str] = None
    local_filename: Optional[str] = None
    local_filepath: Optional[str] = None
    extra_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "media_type": self.media_type.value,
            "url": self.url,
            "title": self.title,
            "extension": self.extension,
            "width": self.width,
            "height": self.height,
            "filesize_bytes": self.filesize_bytes,
            "duration_seconds": self.duration_seconds,
            "local_filename": self.local_filename,
            "local_filepath": self.local_filepath,
            "extra_data": self.extra_data,
        }


@dataclass
class ExtractionResult:
    """Represents the complete result of an extraction operation."""
    platform: str
    source_url: str
    author: str = "unknown"
    author_id: Optional[str] = None
    title: str = ""
    activity_name: str = ""
    caption: str = ""
    upload_date: Optional[str] = None
    media_items: List[MediaItem] = field(default_factory=list)
    target_dir: str = ""
    metadata_file: Optional[str] = None
    post_content_file: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    downloaded_files: List[str] = field(default_factory=list)

    @property
    def total_items(self) -> int:
        return len(self.media_items)

    @property
    def total_downloaded(self) -> int:
        return len(self.downloaded_files)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform,
            "source_url": self.source_url,
            "author": self.author,
            "author_id": self.author_id,
            "title": self.title,
            "activity_name": self.activity_name,
            "caption": self.caption,
            "upload_date": self.upload_date,
            "total_items": self.total_items,
            "target_dir": self.target_dir,
            "metadata_file": self.metadata_file,
            "post_content_file": self.post_content_file,
            "success": self.success,
            "error_message": self.error_message,
            "downloaded_files": self.downloaded_files,
            "media_items": [item.to_dict() for item in self.media_items],
        }

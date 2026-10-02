"""
File utility functions: path sanitization, folder management, image format conversion.
"""

import io
import os
import re
from typing import Optional
from PIL import Image


def sanitize_filename(name: str, max_length: int = 150) -> str:
    """
    Cleans a string to be safely used as a filename across Windows, macOS, and Linux.
    Removes invalid characters and trims excess whitespace.
    """
    if not name:
        return "media_item"
    # Replace invalid Windows filename characters: \ / : * ? " < > |
    cleaned = re.sub(r'[\\/*?:"<>|]', '_', name)
    # Replace control characters and collapse multiple whitespace/underscores
    cleaned = re.sub(r'[\x00-\x1f\x7f]', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = re.sub(r'_+', '_', cleaned).strip(' ._')
    if not cleaned:
        cleaned = "media_item"
    return cleaned[:max_length]


def ensure_unique_filepath(target_path: str) -> str:
    """
    Checks if a file exists; if so, appends an incrementing counter (e.g. file_1.jpg).
    """
    if not os.path.exists(target_path):
        return target_path

    directory, filename = os.path.split(target_path)
    base, ext = os.path.splitext(filename)
    counter = 1
    while True:
        candidate = os.path.join(directory, f"{base}_{counter}{ext}")
        if not os.path.exists(candidate):
            return candidate
        counter += 1


def convert_image_to_jpg(
    source_bytes_or_path: bytes | str,
    target_jpg_path: str,
    quality: int = 95
) -> Optional[str]:
    """
    Converts raw image bytes or an image file to a pristine JPEG format.
    Handles WebP, PNG, AVIF transparency by creating an RGB background.
    """
    try:
        if isinstance(source_bytes_or_path, bytes):
            image = Image.open(io.BytesIO(source_bytes_or_path))
        else:
            image = Image.open(source_bytes_or_path)

        with image:
            # Handle RGBA / Palette mode transparency
            if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
                rgb_im = Image.new("RGB", image.size, (255, 255, 255))
                if image.mode == "P":
                    image = image.convert("RGBA")
                rgb_im.paste(image, mask=image.split()[3])
            else:
                rgb_im = image.convert("RGB")

            os.makedirs(os.path.dirname(os.path.abspath(target_jpg_path)), exist_ok=True)
            rgb_im.save(target_jpg_path, "JPEG", quality=quality, subsampling=0)
            return target_jpg_path
    except Exception:
        return None


def format_bytes(num_bytes: Optional[int]) -> str:
    """Formats raw bytes into human-readable KB, MB, or GB."""
    if num_bytes is None or num_bytes <= 0:
        return "Unknown size"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if num_bytes < 1024.0:
            return f"{num_bytes:.1f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.1f} TB"

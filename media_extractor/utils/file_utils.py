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


def extract_activity_name(caption: str = "", title: str = "", fallback: str = "Activity") -> str:
    """
    Intelligently extracts the activity / event name from post caption or title.
    Supports English & Swahili event keywords (e.g. Mkutano, Uzinduzi, Warsha, Kikao, Ziara, Kongamano,
    Meeting, Workshop, Conference, Launch, Celebration, Clinic, Training, etc.)
    Falls back to the first clean headline/sentence.
    """
    text = (caption or "").strip() or (title or "").strip()
    if not text:
        return sanitize_filename(fallback)

    # 1. Search for explicit activity keywords in Swahili and English
    pattern = (
        r'\b((?:Mkutano wa|Uzinduzi wa|Warsha ya|Kongamano la|Kikao cha|Ziara ya|'
        r'Kliniki ya|Maadhimisho ya|Sherehe za|Semina ya|Jukwaa la|Jukwa la|Mafunzo ya|'
        r'Meeting of|Workshop on|Conference on|Launch of|Visit of|Celebration of|'
        r'Training on|Forum of|Symposium on)\s+[^\n\.\,\!\?]+?)(?=\s+(?:umeanza|umefanyika|imezinduliwa|imezindua|unalenga|uliofanyika|unaoendelea|ambao|ambayo|katika|leo|tarehe|kwa\s+ajili|started|held|taking\s+place|\.|\,|\!|\?|\n|$))'
    )
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        fallback_pattern = (
            r'\b(?:Mkutano wa|Uzinduzi wa|Warsha ya|Kongamano la|Kikao cha|Ziara ya|'
            r'Kliniki ya|Maadhimisho ya|Sherehe za|Semina ya|Jukwaa la|Jukwa la|Mafunzo ya|'
            r'Meeting of|Workshop on|Conference on|Launch of|Visit of|Celebration of|'
            r'Training on|Forum of|Symposium on)\s+[^\n\.\,\!\?]+'
        )
        match = re.search(fallback_pattern, text, re.IGNORECASE)

    if match:
        act = match.group(1 if match.lastindex else 0).strip()
        # Clean hashtags, emojis, extra symbols
        act = re.sub(r'#\w+', '', act)
        act = re.sub(r'@\w+', '', act)
        act = re.sub(r'[^\w\s\-,.()/\'"]', '', act)
        act = re.sub(r'\s+', ' ', act).strip(' ._-,')
        if len(act) > 65:
            words = act[:65].split()
            act = " ".join(words[:-1]) if len(words) > 1 else act[:65]
        if len(act) >= 8:
            return sanitize_filename(act)

    # 2. Extract first headline line or first sentence
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines:
        headline = lines[0]
        # Remove URLs
        headline = re.sub(r'https?://\S+', '', headline)
        headline = re.sub(r'#\w+', '', headline)
        headline = re.sub(r'@\w+', '', headline)
        headline = re.sub(r'[^\w\s\-,.()/\'"]', '', headline)
        headline = re.sub(r'\s+', ' ', headline).strip(' ._-,')

        if len(headline) > 75:
            # Cut at period or comma if available
            p_idx = headline.find('.')
            if 15 < p_idx <= 75:
                headline = headline[:p_idx].strip()
            else:
                c_idx = headline.find(',')
                if 20 < c_idx <= 75:
                    headline = headline[:c_idx].strip()
                else:
                    words = headline[:75].split()
                    headline = " ".join(words[:-1]) if len(words) > 1 else headline[:75]
        if headline:
            return sanitize_filename(headline)

    return sanitize_filename(fallback)


def format_post_date(date_raw: Optional[str | int | float] = None) -> str:
    """Formats date as YYYY-MM-DD from timestamp, iso string, or default to current date."""
    from datetime import datetime
    if date_raw:
        # Check if unix timestamp
        if isinstance(date_raw, (int, float)) or (isinstance(date_raw, str) and date_raw.isdigit()):
            try:
                ts = float(date_raw)
                return datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
            except Exception:
                pass
        # Check if YYYYMMDD string
        if isinstance(date_raw, str) and len(date_raw) == 8 and date_raw.isdigit():
            return f"{date_raw[:4]}-{date_raw[4:6]}-{date_raw[6:]}"
        # Check if already contains date
        m = re.search(r'\b(20\d{2})[-/.](0[1-9]|1[0-2])[-/.](0[1-9]|[12]\d|3[01])\b', str(date_raw))
        if m:
            return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d")


def resolve_activity_folder(
    base_output_dir: str,
    caption: str = "",
    title: str = "",
    fallback_author: str = "Media",
    date_raw: Optional[str | int | float] = None,
    custom_folder_name: Optional[str] = None
) -> str:
    """
    Resolves the destination folder path using the activity name and date.
    E.g.: 'Mkutano wa Jukwa la NGOs Mkoa Tanga - 2026-09-29'
    """
    if custom_folder_name and custom_folder_name.strip():
        folder_name = sanitize_filename(custom_folder_name.strip())
    else:
        activity = extract_activity_name(caption, title=title, fallback=fallback_author)
        date_str = format_post_date(date_raw)
        folder_name = sanitize_filename(f"{activity} - {date_str}")

    return os.path.join(base_output_dir, folder_name)


def write_post_content_txt(
    target_dir: str,
    title: str,
    author: str,
    platform: str,
    url: str,
    date_str: str,
    caption: str,
    downloaded_files: Optional[list] = None,
    filename: str = "post_content.txt"
) -> str:
    """
    Writes a clean, structured post_content.txt with post metadata and caption.
    """
    os.makedirs(target_dir, exist_ok=True)
    file_path = os.path.join(target_dir, filename)

    lines = [
        "=" * 80,
        f"ACTIVITY / TITLE : {title or 'Social Media Post'}",
        f"PLATFORM         : {platform}",
        f"AUTHOR / PROFILE : @{author}",
        f"DATE             : {date_str}",
        f"SOURCE URL       : {url}",
        "=" * 80,
        "",
        "POST CONTENT / CAPTION:",
        "-" * 80,
        caption.strip() if caption else "(No caption provided in post)",
        "",
        "-" * 80,
        f"EXTRACTED ASSETS SUMMARY ({len(downloaded_files) if downloaded_files else 0} files):",
    ]

    if downloaded_files:
        for idx, fp in enumerate(downloaded_files, start=1):
            sz = format_bytes(os.path.getsize(fp)) if os.path.exists(fp) else "N/A"
            lines.append(f"  [{idx:02d}] {os.path.basename(fp)} ({sz})")
    else:
        lines.append("  (No files downloaded)")

    lines.append("=" * 80)
    lines.append("")

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return file_path

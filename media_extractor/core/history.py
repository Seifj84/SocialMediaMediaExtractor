"""
History and Log Record Tracker for OmniMedia.
Maintains persistent records of all extraction attempts, successes, failures,
downloaded files, and diagnostics.
"""

import json
import os
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

from .models import ExtractionResult, MediaFilter, MediaQuality


def _get_history_file_path() -> str:
    """Returns path to persistent history.json storage."""
    base_dir = os.path.join(os.path.expanduser("~"), ".omni_media")
    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, "history.json")


def _get_log_file_path() -> str:
    """Returns path to human-readable activity.log file."""
    base_dir = os.path.join(os.path.expanduser("~"), ".omni_media")
    os.makedirs(base_dir, exist_ok=True)
    return os.path.join(base_dir, "activity.log")


class HistoryTracker:
    """Manages persistent logging and audit records for extraction events."""

    def __init__(self, history_file: Optional[str] = None):
        self.history_file = history_file or _get_history_file_path()
        self.log_file = _get_log_file_path()

    def record(
        self,
        result: ExtractionResult,
        media_filter: MediaFilter = MediaFilter.ALL,
        quality: MediaQuality = MediaQuality.BEST,
        duration_seconds: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Records an extraction attempt to both JSON history and the text log file.
        """
        now = datetime.now()
        timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")

        total_bytes = 0
        file_details = []
        for fp in result.downloaded_files:
            sz = 0
            if os.path.exists(fp):
                sz = os.path.getsize(fp)
                total_bytes += sz
            file_details.append({
                "filename": os.path.basename(fp),
                "path": fp,
                "size_bytes": sz,
            })

        status_str = "SUCCESS" if (result.success and len(result.downloaded_files) > 0) else ("EMPTY" if result.success else "FAILED")

        entry = {
            "id": f"rec_{int(time.time() * 1000)}",
            "timestamp": timestamp_str,
            "url": result.source_url,
            "platform": result.platform,
            "status": status_str,
            "author": result.author,
            "title": result.title,
            "target_dir": result.target_dir,
            "filter": media_filter.value if hasattr(media_filter, 'value') else str(media_filter),
            "quality": quality.value if hasattr(quality, 'value') else str(quality),
            "total_files": len(result.downloaded_files),
            "total_bytes": total_bytes,
            "files": file_details,
            "duration_seconds": round(duration_seconds, 2),
            "error_message": result.error_message or "",
        }

        # 1. Update JSON storage
        history = self.get_all()
        history.insert(0, entry)  # Prepend newest first
        # Keep last 500 records
        if len(history) > 500:
            history = history[:500]

        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

        # 2. Append to human-readable log file
        try:
            with open(self.log_file, "a", encoding="utf-8") as lf:
                log_line = (
                    f"[{timestamp_str}] [{status_str:<7}] Platform: {result.platform:<10} | "
                    f"Files: {len(result.downloaded_files):<2} | "
                    f"Duration: {round(duration_seconds, 1)}s | "
                    f"URL: {result.source_url}"
                )
                if result.error_message:
                    log_line += f" | Error: {result.error_message}"
                lf.write(log_line + "\n")
        except Exception:
            pass

        return entry

    def get_all(self) -> List[Dict[str, Any]]:
        """Returns all history records sorted by newest first."""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def get_stats(self) -> Dict[str, Any]:
        """Calculates summary statistics across all past extractions."""
        records = self.get_all()
        total = len(records)
        success_count = sum(1 for r in records if r.get("status") == "SUCCESS")
        failed_count = sum(1 for r in records if r.get("status") == "FAILED")
        empty_count = sum(1 for r in records if r.get("status") == "EMPTY")
        total_files = sum(r.get("total_files", 0) for r in records)
        total_bytes = sum(r.get("total_bytes", 0) for r in records)

        success_rate = round((success_count / total * 100), 1) if total > 0 else 0.0

        return {
            "total_runs": total,
            "success_count": success_count,
            "failed_count": failed_count,
            "empty_count": empty_count,
            "success_rate_percent": success_rate,
            "total_files_downloaded": total_files,
            "total_bytes_downloaded": total_bytes,
        }

    def clear(self) -> bool:
        """Clears all history records."""
        try:
            if os.path.exists(self.history_file):
                os.remove(self.history_file)
            return True
        except Exception:
            return False


_GLOBAL_TRACKER: Optional[HistoryTracker] = None


def get_history_tracker() -> HistoryTracker:
    """Returns the singleton HistoryTracker instance."""
    global _GLOBAL_TRACKER
    if _GLOBAL_TRACKER is None:
        _GLOBAL_TRACKER = HistoryTracker()
    return _GLOBAL_TRACKER

"""
Tests for history tracker and audit records.
"""

import os
import tempfile
from media_extractor.core.history import HistoryTracker
from media_extractor.core.models import ExtractionResult, MediaFilter, MediaQuality


def test_history_tracker_records_success():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        temp_path = tf.name

    try:
        tracker = HistoryTracker(history_file=temp_path)
        res = ExtractionResult(
            platform="Instagram",
            source_url="https://instagram.com/p/test12345",
            author="test_user",
            title="Test Post",
            downloaded_files=[],
            success=True,
        )

        entry = tracker.record(res, media_filter=MediaFilter.ALL, quality=MediaQuality.BEST, duration_seconds=1.5)
        assert entry["status"] == "EMPTY"
        assert entry["platform"] == "Instagram"

        stats = tracker.get_stats()
        assert stats["total_runs"] == 1
        assert stats["empty_count"] == 1

        all_records = tracker.get_all()
        assert len(all_records) == 1
        assert all_records[0]["url"] == "https://instagram.com/p/test12345"

        tracker.clear()
        assert len(tracker.get_all()) == 0
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

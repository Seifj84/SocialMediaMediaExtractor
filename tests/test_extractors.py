"""
Tests for ExtractorManager and individual extractor URL recognition.
"""

from media_extractor.extractors.manager import ExtractorManager
from media_extractor.extractors.instagram import InstagramExtractor


def test_extractor_manager_routing():
    mgr = ExtractorManager()

    urls_to_expected = [
        ("https://www.instagram.com/p/C678abcd/", "Instagram"),
        ("https://instagram.com/reel/C890xyz/", "Instagram"),
        ("https://www.tiktok.com/@creator/video/7123456789012345678", "TikTok"),
        ("https://vt.tiktok.com/ZS2abcd/", "TikTok"),
        ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "YouTube"),
        ("https://youtu.be/dQw4w9WgXcQ", "YouTube"),
        ("https://youtube.com/shorts/abc123def", "YouTube"),
        ("https://twitter.com/user/status/1234567890123456789", "Twitter/X"),
        ("https://x.com/user/status/1234567890123456789", "Twitter/X"),
        ("https://www.facebook.com/reel/123456789", "Facebook"),
        ("https://fb.watch/abcd1234/", "Facebook"),
        ("https://reddit.com/r/photography/comments/abcdef/sample_title/", "Reddit"),
        ("https://pinterest.com/pin/123456789012345678/", "Pinterest"),
        ("https://vimeo.com/123456789", "Universal"),
    ]

    for url, expected_name in urls_to_expected:
        ext = mgr.get_extractor(url)
        assert ext.platform_name == expected_name, f"Failed for {url}: got {ext.platform_name}, expected {expected_name}"


def test_instagram_shortcode_extraction():
    extractor = InstagramExtractor()
    assert extractor.extract_shortcode("https://www.instagram.com/p/DdoWS1KCGwA/?igsh=abc") == "DdoWS1KCGwA"
    assert extractor.extract_shortcode("https://instagram.com/reel/DdoWS1KCGwA/") == "DdoWS1KCGwA"

import unittest
from unittest import mock

from moodeng.config import get_config
from moodeng.detector import Monitor, _label_candidates, _normalize_remote_url


class DetectorHelpersTest(unittest.TestCase):
    def test_label_candidates_include_common_sea_lion_aliases(self):
        candidates = _label_candidates("STELLAR SEA LIONS")
        self.assertIn("stellar sea lions", candidates)
        self.assertIn("steller sea lion", candidates)

    def test_normalize_remote_url_adds_https_to_scheme_relative_urls(self):
        self.assertEqual(
            _normalize_remote_url("//img.hdrelay.com/"),
            "https://img.hdrelay.com/",
        )
        self.assertEqual(
            _normalize_remote_url("https://img.hdrelay.com/"),
            "https://img.hdrelay.com/",
        )

    def test_get_config_accepts_legacy_youtube_url_alias(self):
        config = get_config({"youtube_url": "https://example.com/live"})
        self.assertEqual(config["source_url"], "https://example.com/live")

    def test_resolve_source_keeps_direct_stream_urls(self):
        monitor = Monitor.__new__(Monitor)
        resolved = monitor._resolve_source("rtsp://example.com/live")
        self.assertEqual(
            resolved,
            {"kind": "video_capture", "capture_url": "rtsp://example.com/live"},
        )

    def test_resolve_source_uses_hdrelay_resolver_for_pier39(self):
        monitor = Monitor.__new__(Monitor)
        expected = {"kind": "hdrelay_frames", "camera_id": "cid"}
        with mock.patch.object(
            monitor,
            "_resolve_hdrelay_page_source",
            return_value=expected,
        ) as resolve_hdrelay:
            resolved = monitor._resolve_source("https://www.pier39.com/sealions/")

        resolve_hdrelay.assert_called_once_with("https://www.pier39.com/sealions/")
        self.assertEqual(resolved, expected)

    def test_resolve_source_falls_back_to_yt_dlp_for_supported_pages(self):
        monitor = Monitor.__new__(Monitor)
        with mock.patch.object(
            monitor,
            "_get_stream_url",
            return_value="https://cdn.example.com/stream.m3u8",
        ) as get_stream_url:
            resolved = monitor._resolve_source("https://example.com/watch")

        get_stream_url.assert_called_once_with("https://example.com/watch")
        self.assertEqual(
            resolved,
            {
                "kind": "video_capture",
                "capture_url": "https://cdn.example.com/stream.m3u8",
            },
        )


if __name__ == "__main__":
    unittest.main()

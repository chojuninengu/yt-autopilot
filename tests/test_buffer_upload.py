"""Unit tests for Buffer upload module."""
import json
import os
import pathlib
import sys
import unittest
from unittest.mock import MagicMock, patch

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import buffer_upload  # noqa: E402


class TestBufferUpload(unittest.TestCase):
    def test_missing_token_raises(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(RuntimeError) as ctx:
                buffer_upload.get_buffer_token()
            self.assertIn("BUFFER_ACCESS_TOKEN", str(ctx.exception))

    @patch("buffer_upload.execute_graphql")
    def test_get_channels(self, mock_gql):
        mock_gql.side_effect = [
            {"account": {"id": "acc1", "organizations": [{"id": "org1", "name": "Org"}]}},
            {"channels": [{"id": "ch1", "name": "TikTok Channel", "service": "tiktok", "displayName": "TikTok"}]}
        ]
        channels = buffer_upload.get_channels()
        self.assertEqual(len(channels), 1)
        self.assertEqual(channels[0]["service"], "tiktok")

    @patch("buffer_upload.get_channels")
    def test_dry_run_post(self, mock_get_channels):
        mock_get_channels.return_value = [
            {"id": "ch_tt", "name": "Test TikTok", "service": "tiktok"}
        ]
        res = buffer_upload.post_video_to_buffer(
            video_url="https://example.com/video.mp4",
            text="Test TikTok caption #fyp",
            service="tiktok",
            dry_run=True
        )
        self.assertTrue(res["dry_run"])
        self.assertEqual(res["channel_id"], "ch_tt")


if __name__ == "__main__":
    unittest.main()

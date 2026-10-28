"""Unit tests for image generation module, prompt sanitization, motion filters, and offline rendering."""
import base64
import json
import os
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from imagegen import sanitize_prompt, generate_image, _generate_cloudflare, _generate_together  # noqa: E402
from render import build_motion_filter, render_video  # noqa: E402
from ideate import validate_and_sanitize_plan, VALID_MOTIONS  # noqa: E402


class TestImageGen(unittest.TestCase):
    def setUp(self):
        self.cfg = {
            "art_style": "bold 2D cartoon, thick outlines, bright saturated colors, vertical 9:16",
            "character": {
                "name": "Pip",
                "description": "A small energetic blue robot with glowing yellow antenna"
            },
            "image_providers": ["cloudflare", "together", "pollinations"],
            "blocked_terms": ["mrbeast", "mr beast"],
            "disclose_ai_in_description": True,
            "visual_mode": "cartoon_stills"
        }

    def test_prompt_composition_and_blocked_terms(self):
        raw = "Pip is watching MrBeast do a challenge with mr beast at a desk"
        sanitized = sanitize_prompt(
            raw,
            art_style=self.cfg["art_style"],
            char_desc=self.cfg["character"]["description"],
            blocked_terms=self.cfg["blocked_terms"]
        )
        self.assertIn("bold 2D cartoon", sanitized)
        self.assertIn("A small energetic blue robot", sanitized)
        self.assertNotIn("MrBeast", sanitized)
        self.assertNotIn("mr beast", sanitized)
        self.assertNotIn("mrbeast", sanitized.lower())

    def test_skip_on_missing_secret(self):
        # Cloudflare and Together should raise ValueError when secrets are missing
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                _generate_cloudflare("test prompt")
            with self.assertRaises(ValueError):
                _generate_together("test prompt")

    def test_provider_fallback_order(self):
        # Mock providers where cloudflare fails, together fails, and pollinations succeeds
        mock_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 2000

        with patch("imagegen._generate_cloudflare", side_effect=Exception("CF error")), \
             patch("imagegen._generate_together", side_effect=Exception("Together error")), \
             patch("imagegen._generate_pollinations", return_value=mock_png):

            with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
                out_path = pathlib.Path(tmp.name)
                provider = generate_image("Test prompt", out_path, self.cfg)
                self.assertEqual(provider, "pollinations")
                self.assertTrue(out_path.exists())
                self.assertEqual(out_path.read_bytes(), mock_png)

    def test_retry_on_429_then_succeed(self):
        mock_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 2000
        mock_resp_429 = MagicMock()
        mock_resp_429.status_code = 429
        mock_ex_429 = Exception("Rate limited")
        mock_ex_429.response = mock_resp_429

        attempts = []

        def cf_side_effect(*args, **kwargs):
            attempts.append(1)
            if len(attempts) < 2:
                raise mock_ex_429
            return mock_png

        with patch("imagegen._generate_cloudflare", side_effect=cf_side_effect), \
             patch("time.sleep"):  # skip actual sleep
            with tempfile.NamedTemporaryFile(suffix=".png") as tmp:
                out_path = pathlib.Path(tmp.name)
                provider = generate_image("Retry prompt", out_path, self.cfg)
                self.assertEqual(provider, "cloudflare")
                self.assertEqual(len(attempts), 2)

    def test_phase1_validation_defaults(self):
        # Incomplete/empty plan
        bad_plan = {
            "scenes": [
                {"narration": "First scene without prompt or motion"},
                {"narration": "Second scene", "motion": "invalid_motion"}
            ]
        }
        sanitized = validate_and_sanitize_plan(bad_plan)
        self.assertIn("picked_trend", sanitized)
        self.assertEqual(len(sanitized["scenes"]), 2)

        # Scene 0 should have defaulted image_prompt from narration and motion from VALID_MOTIONS
        self.assertIn("First scene", sanitized["scenes"][0]["image_prompt"])
        self.assertEqual(sanitized["scenes"][0]["motion"], VALID_MOTIONS[0])

        # Scene 1 had invalid motion, should be replaced by VALID_MOTIONS[1]
        self.assertEqual(sanitized["scenes"][1]["motion"], VALID_MOTIONS[1])

    def test_motion_filter_strings(self):
        for m in VALID_MOTIONS:
            vf = build_motion_filter(m, duration_sec=2.5, fps=30)
            self.assertIn("scale=2160:3840", vf)
            self.assertIn("zoompan=", vf)
            self.assertIn("d=75", vf)  # 2.5s * 30fps = 75 frames

    def test_dry_run_render_offline(self):
        # Test full render with mock visual assets (0 network required)
        plan = {
            "video_title": "Dry Run Test Video",
            "script": "Testing offline render with animated cartoon stills.",
            "scenes": [
                {
                    "narration": "Testing scene one.",
                    "visual_keywords": ["robot", "code"],
                    "image_prompt": "Pip the robot waving",
                    "motion": "zoom_in"
                },
                {
                    "narration": "Testing scene two.",
                    "visual_keywords": ["matrix", "screen"],
                    "image_prompt": "Pip the robot looking at blueprints",
                    "motion": "pan_left"
                }
            ]
        }
        cfg = dict(self.cfg)
        cfg["dry_run"] = True

        with tempfile.NamedTemporaryFile(suffix=".mp4") as tmp:
            out_path = pathlib.Path(tmp.name)
            res = render_video(plan, out_path, cfg=cfg)
            self.assertTrue(res.exists())
            self.assertGreater(res.stat().st_size, 1000)
            # Verify provider recorded
            self.assertEqual(plan["scenes"][0]["provider"], "mock_placeholder")
            self.assertEqual(plan["scenes"][1]["provider"], "mock_placeholder")

    def test_youtube_credentials_parsing(self):
        import youtube_upload
        valid_data = {
            "token": "fake_token",
            "refresh_token": "fake_refresh",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "fake_client_id",
            "client_secret": "fake_client_secret",
            "scopes": ["https://www.googleapis.com/auth/youtube.upload"]
        }

        with patch("google.oauth2.credentials.Credentials.refresh"):
            # Test with raw JSON string in YOUTUBE_TOKEN
            with patch.dict(os.environ, {"YOUTUBE_TOKEN": json.dumps(valid_data)}):
                with patch("pathlib.Path.exists", return_value=False):
                    creds = youtube_upload.get_credentials()
                    self.assertEqual(creds.client_id, "fake_client_id")

            # Test with quote-wrapped JSON string
            with patch.dict(os.environ, {"YOUTUBE_TOKEN": f"'{json.dumps(valid_data)}'"}):
                with patch("pathlib.Path.exists", return_value=False):
                    creds = youtube_upload.get_credentials()
                    self.assertEqual(creds.client_id, "fake_client_id")

            # Test with base64 encoded JSON string
            import base64
            b64_str = base64.b64encode(json.dumps(valid_data).encode("utf-8")).decode("utf-8")
            with patch.dict(os.environ, {"YOUTUBE_TOKEN": b64_str}):
                with patch("pathlib.Path.exists", return_value=False):
                    creds = youtube_upload.get_credentials()
                    self.assertEqual(creds.client_id, "fake_client_id")

            # Test with client_secrets detection
            with patch.dict(os.environ, {"YOUTUBE_TOKEN": json.dumps({"installed": {}})}):
                with patch("pathlib.Path.exists", return_value=False):
                    with self.assertRaises(RuntimeError) as ctx:
                        youtube_upload.get_credentials()
                    self.assertIn("client_secrets.json", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()

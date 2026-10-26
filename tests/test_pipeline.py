"""Unit tests for yt-autopilot pipeline."""
import json
import os
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from scout import collect  # noqa: E402
from ideate import get_mock_plan, ideate  # noqa: E402


class TestYtAutopilot(unittest.TestCase):
    def setUp(self):
        self.config_path = ROOT / "config.json"
        self.assertTrue(self.config_path.exists(), "config.json must exist")
        self.cfg = json.loads(self.config_path.read_text())

    def test_config_structure(self):
        expected_keys = [
            "niche", "language", "google_trends_geo",
            "reddit_subs", "hn_limit", "trends_limit",
            "reddit_limit", "target_seconds"
        ]
        for key in expected_keys:
            self.assertIn(key, self.cfg)

    def test_mock_ideation_schema(self):
        sample_items = [
            {"source": "google_trends_US", "title": "Breakthrough in Fusion Energy", "traffic": "500K+"},
            {"source": "hackernews", "title": "Show HN: Fast Vector Search in C", "score": 300}
        ]
        plan = ideate(sample_items, self.cfg, mock=True)

        required_keys = [
            "picked_trend", "why_viral", "core_idea",
            "video_title", "script", "scenes",
            "youtube", "tiktok"
        ]
        for key in required_keys:
            self.assertIn(key, plan)

        self.assertIsInstance(plan["scenes"], list)
        self.assertGreater(len(plan["scenes"]), 0)
        for scene in plan["scenes"]:
            self.assertIn("narration", scene)
            self.assertIn("visual_keywords", scene)

        self.assertIn("title", plan["youtube"])
        self.assertIn("description", plan["youtube"])
        self.assertIn("hashtags", plan["youtube"])
        self.assertIn("caption", plan["tiktok"])
        self.assertIn("hashtags", plan["tiktok"])

    def test_cli_dry_run_execution(self):
        # Run python src/run_phase1.py --dry-run
        res = subprocess.run(
            [sys.executable, str(ROOT / "src" / "run_phase1.py"), "--dry-run"],
            cwd=str(ROOT),
            capture_output=True,
            text=True
        )
        self.assertEqual(res.returncode, 0, f"Command failed with output: {res.stdout}\n{res.stderr}")
        self.assertIn("Done:", res.stdout)

        # Verify output directory contains files
        output_files = list((ROOT / "output").glob("*-plan.md"))
        self.assertGreater(len(output_files), 0, "Plan markdown file should be generated")


if __name__ == "__main__":
    unittest.main()

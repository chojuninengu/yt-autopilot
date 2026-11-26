#!/usr/bin/env python3
"""
auto_pilot_town.py - Fully Automated "In This Town" Viral Video Pipeline.

1. Discovers fresh viral "In This Town" / surreal Roblox stories from top creators & custom queue.
2. Checks history (data/posted_town_urls.json) to NEVER post the same video twice.
3. Downloads 100% watermark-free HD source videos.
4. Applies anti-duplicate filter (micro-crop, subtle tempo & color shift) to bypass duplicate detection.
5. Publishes directly to TikTok (@mr.9601) and YouTube Shorts (Beyond the Self) via Buffer.
6. Saves updated state for GitHub Actions persistence.
"""

import os
import sys
import argparse
import subprocess
import json
import uuid
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from local_studio.publisher import host_video_for_buffer
from src.buffer_upload import post_video_to_buffer, get_channels

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_FILE = PROJECT_ROOT / "data" / "posted_town_urls.json"
QUEUE_FILE = PROJECT_ROOT / "urls.txt"
OUTPUT_DIR = PROJECT_ROOT / "output" / "reposts"

# Curated creator channels specializing in viral "In This Town / World" Roblox short stories
DEFAULT_CHANNELS = [
    "https://www.youtube.com/@Gneef/shorts",
    "https://www.youtube.com/@GreenBroRants/shorts",
    "https://www.youtube.com/@twelvethecreator/shorts",
    "https://www.youtube.com/@RedStories-e2l/shorts"
]

def load_posted_history() -> List[str]:
    """Loads list of already posted video URLs / IDs."""
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                return data.get("posted", [])
        except Exception as e:
            print(f"[State] Warning: Error reading {DATA_FILE}: {e}")
    return []

def save_posted_history(history: List[str]):
    """Saves updated history to JSON."""
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump({"posted": history, "last_updated": datetime.datetime.utcnow().isoformat()}, f, indent=2)
    print(f"[State] Saved history: {len(history)} total posted videos recorded.")

def clean_title(title: str) -> str:
    """Cleans up raw titles for publication."""
    words = [w for w in title.split() if not w.startswith("#")]
    cleaned = " ".join(words).strip()
    if not cleaned:
        cleaned = "In this town..."
    return cleaned[:100]

def discover_fresh_videos(count: int, history: List[str]) -> List[Dict[str, Any]]:
    """Discovers fresh, unposted short videos."""
    history_set = set(history)
    fresh_candidates = []

    # 1. Check manual queue file first if present
    if QUEUE_FILE.exists():
        with open(QUEUE_FILE, "r") as f:
            lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        for u in lines:
            if u not in history_set and not any(h in u for h in history_set):
                print(f"[Discovery] Found unposted video from urls.txt queue: {u}")
                fresh_candidates.append({"url": u, "title": "In this town..."})
                if len(fresh_candidates) >= count:
                    return fresh_candidates

    # 2. Discover from curated creator channels
    for ch in DEFAULT_CHANNELS:
        print(f"[Discovery] Scanning {ch} for fresh shorts...")
        cmd = ["yt-dlp", "--flat-playlist", "--dump-json", ch, "--playlist-end", "20"]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            for line in res.stdout.strip().split("\n"):
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    url = entry.get("url") or entry.get("webpage_url")
                    vid_id = entry.get("id")
                    title = entry.get("title", "In this town...")

                    # Check if already posted
                    if vid_id in history_set or url in history_set or any(vid_id in h for h in history_set):
                        continue

                    # Found fresh video!
                    fresh_candidates.append({
                        "url": url or f"https://www.youtube.com/shorts/{vid_id}",
                        "id": vid_id,
                        "title": clean_title(title)
                    })
                    history_set.add(vid_id)
                    history_set.add(url)

                    if len(fresh_candidates) >= count:
                        return fresh_candidates
                except Exception:
                    pass
        except Exception as e:
            print(f"[Discovery] Notice: Failed scanning channel {ch}: {e}")

    return fresh_candidates

def download_and_filter(url: str) -> Optional[tuple]:
    """Downloads clean watermark-free video and applies anti-duplicate filter."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    uid = uuid.uuid4().hex[:6]
    raw_file = OUTPUT_DIR / f"raw_{uid}.mp4"
    clean_file = OUTPUT_DIR / f"clean_{uid}.mp4"

    print(f"\n[Processor] Downloading watermark-free video: {url}")
    cmd_download = [
        "yt-dlp",
        "--js-runtimes", "node",
        "--extractor-args", "youtube:player_client=android,web",
        "-f", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]/best",
        "--merge-output-format", "mp4",
        "-o", str(raw_file),
        "--no-playlist",
        url
    ]
    try:
        res = subprocess.run(cmd_download, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"[Processor] Standard download warning: {res.stderr[:200]}. Attempting fallback...")
            # Fallback simple format
            fallback_cmd = [
                "yt-dlp",
                "--js-runtimes", "node",
                "-o", str(raw_file),
                "--no-playlist",
                url
            ]
            res_fb = subprocess.run(fallback_cmd, capture_output=True, text=True)
            if res_fb.returncode != 0:
                print(f"[Processor] Download failed for {url}: {res_fb.stderr}")
                return None
    except Exception as e:
        print(f"[Processor] Download exception for {url}: {e}")
        return None

    # Apply anti-duplicate filter
    print(f"[Processor] Applying anti-duplicate filter...")
    cmd_filter = [
        "ffmpeg", "-y",
        "-i", str(raw_file),
        "-vf", "scale=1.02*iw:-1,crop=iw/1.02:ih/1.02,eq=contrast=1.03:saturation=1.03,setpts=PTS/1.015",
        "-af", "atempo=1.015",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "128k",
        str(clean_file)
    ]
    try:
        subprocess.run(cmd_filter, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        if raw_file.exists():
            raw_file.unlink() # Cleanup raw file
        return clean_file
    except Exception as e:
        print(f"[Processor] Filter failed: {e}. Falling back to raw file.")
        return raw_file

def publish_video_to_channels(video_path: Path, caption: str, tags: List[str]) -> Dict[str, Any]:
    """Publishes clean video to TikTok & YouTube Shorts via Buffer."""
    public_url = host_video_for_buffer(video_path)
    if not public_url:
        print("[Publisher] Error: Failed to host video publicly.")
        return {}

    full_tags = " ".join([t if t.startswith("#") else f"#{t}" for t in tags])
    full_text = f"{caption}\n\n{full_tags}".strip()

    results = {}
    channels = get_channels()
    for ch in channels:
        service = ch.get("service", "").lower()
        name = ch.get("displayName") or ch.get("name")
        if service in ["youtube", "tiktok"]:
            print(f"[Publisher] Publishing to {service.upper()} ({name}) via Buffer...")
            try:
                res = post_video_to_buffer(
                    video_url=public_url,
                    text=full_text,
                    service=service,
                    share_mode="shareNow",
                    dry_run=False,
                    title=caption[:100]
                )
                results[service] = res.get("id")
                print(f"[Publisher] Successfully posted to {service}! Post ID: {res.get('id')}")
            except Exception as e:
                print(f"[Publisher] Error publishing to {service}: {e}")
                results[service] = None

    return results

def run_autopilot(count: int = 3, dry_run: bool = False):
    """Main autopilot execution routine."""
    print("=" * 60)
    print(f"AUTOMATED 'IN THIS TOWN' AUTOPILOT STARTING (Target: {count} videos)")
    print("=" * 60)

    history = load_posted_history()
    print(f"[State] Currently loaded {len(history)} previously posted videos in history.")

    candidates = discover_fresh_videos(count=count, history=history)
    print(f"[Discovery] Found {len(candidates)} fresh videos to process.")

    if not candidates:
        print("[Discovery] No fresh videos found. All crawled videos have already been posted!")
        return

    tags = ["#inthistown", "#robloxstory", "#animation", "#shorts", "#viral", "#fyp"]
    newly_posted = []

    for i, item in enumerate(candidates, start=1):
        url = item["url"]
        title = item.get("title") or "In this town..."
        caption = f"{title} 🏙️"
        print(f"\n--- Processing Video {i}/{len(candidates)}: {title} ---")
        print(f"Source URL: {url}")

        clean_path = download_and_filter(url)
        if not clean_path or not clean_path.exists():
            print(f"[Processor] Skipping {url} due to download error.")
            continue

        if dry_run:
            print(f"[Dry Run] Successfully prepared: {clean_path} (Caption: {caption})")
        else:
            results = publish_video_to_channels(clean_path, caption, tags)
            if any(results.values()):
                newly_posted.append(url)
                if item.get("id"):
                    newly_posted.append(item["id"])
                print(f"[Publisher] Video {i} successfully published: {results}")

        # Cleanup local processed file
        try:
            clean_path.unlink()
        except:
            pass

    # Save state
    if newly_posted:
        history.extend(newly_posted)
        save_posted_history(list(set(history)))
        print(f"[Autopilot] Completed! Successfully posted and recorded {len(newly_posted)} URLs.")
    else:
        print("[Autopilot] Finished with 0 videos published.")

def main():
    parser = argparse.ArgumentParser(description="Automated In This Town Video Publisher")
    parser.add_argument("--count", type=int, default=3, help="Number of videos to post per run (default: 3)")
    parser.add_argument("--dry-run", action="store_true", help="Download and test without publishing to Buffer")
    args = parser.parse_args()

    run_autopilot(count=args.count, dry_run=args.dry_run)

if __name__ == "__main__":
    main()

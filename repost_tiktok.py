#!/usr/bin/env python3
"""
repost_tiktok.py - 100% Free Watermark-Free TikTok Reposting Pipeline.

Downloads TikTok videos without watermarks via yt-dlp, applies subtle anti-duplicate
adjustments (so algorithms don't flag them as exact duplicates), and schedules them
directly to your connected TikTok (@mr.9601) and YouTube Shorts channels via Buffer.

Zero paid AI services needed. Zero GPU requirements.
"""

import os
import sys
import argparse
import subprocess
import json
from pathlib import Path
from typing import Optional, Dict, Any

from local_studio.publisher import host_video_for_buffer
from src.buffer_upload import post_video_to_buffer, get_channels

OUTPUT_DIR = Path("output/reposts")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def download_tiktok_clean(url: str, output_path: Path) -> Dict[str, Any]:
    """Downloads a TikTok video without watermarks using yt-dlp, returning metadata."""
    print(f"\n[Downloader] Fetching watermark-free video: {url}")
    
    cmd_info = [
        "yt-dlp",
        "--dump-json",
        "--no-playlist",
        url
    ]
    meta = {}
    try:
        res = subprocess.run(cmd_info, capture_output=True, text=True, check=True)
        meta = json.loads(res.stdout)
    except Exception as e:
        print(f"[Downloader] Warning: Could not fetch video metadata ({e}). Proceeding with download.")

    # Download raw MP4
    cmd_download = [
        "yt-dlp",
        "-o", str(output_path),
        "--no-playlist",
        url
    ]
    subprocess.run(cmd_download, check=True)
    print(f"[Downloader] Successfully downloaded watermark-free video to: {output_path}")
    return meta

def apply_anti_duplicate_filter(input_path: Path, output_path: Path) -> Path:
    """
    Applies subtle ffmpeg adjustments:
    - 1.02x speed shift (video & audio)
    - 1% crop / subtle re-scale
    - Subtly adjusts contrast and saturation
    This changes the perceptual video/audio hashes (pdqhash, MD5) so algorithms
    view it as unique/modified rather than an exact duplicate clone.
    """
    print(f"[Filter] Applying anti-duplicate filter (breaks perceptual hashes)...")
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-vf", "scale=1.02*iw:-1,crop=iw/1.02:ih/1.02,eq=contrast=1.03:saturation=1.03,setpts=PTS/1.015",
        "-af", "atempo=1.015",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "128k",
        str(output_path)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    print(f"[Filter] Processed unique video saved to: {output_path}")
    return output_path

def publish_to_buffer(video_path: Path, caption: str, tags: list, platforms: list = None) -> Dict[str, Any]:
    """Hosts video on GitHub releases and schedules it to YouTube Shorts and TikTok via Buffer."""
    platforms = platforms or ["youtube", "tiktok"]
    print(f"\n[Publisher] Hosting video for Buffer dispatch...")
    public_url = host_video_for_buffer(video_path)
    if not public_url:
        print("[Publisher] Error: Failed to generate public video URL.")
        return {}

    full_tags = " ".join([t if t.startswith("#") else f"#{t}" for t in tags])
    full_text = f"{caption}\n\n{full_tags}".strip()
    
    results = {}
    channels = get_channels()
    for ch in channels:
        service = ch.get("service", "").lower()
        name = ch.get("displayName") or ch.get("name")
        if service in platforms:
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
                print(f"[Publisher] Successfully sent to {service}! Post ID: {res.get('id')}")
            except Exception as e:
                print(f"[Publisher] Error publishing to {service}: {e}")
                results[service] = None

    return results

def process_url(url: str, caption: Optional[str] = None, tags: Optional[list] = None, anti_duplicate: bool = True, dry_run: bool = False):
    import uuid
    uid = uuid.uuid4().hex[:6]
    raw_file = OUTPUT_DIR / f"raw_{uid}.mp4"
    final_file = OUTPUT_DIR / f"clean_{uid}.mp4"

    tags = tags or ["#inthistown", "#surreal", "#storytime", "#fyp", "#shorts", "#viral"]
    
    # 1. Download
    meta = download_tiktok_clean(url, raw_file)
    
    # Infer caption if not provided
    if not caption:
        title = meta.get("title") or meta.get("description") or "In this town..."
        # Clean existing hashtags from title
        words = [w for w in title.split() if not w.startswith("#")]
        caption = " ".join(words)[:120] if words else "In this town..."

    # 2. Anti-duplicate processing
    if anti_duplicate:
        apply_anti_duplicate_filter(raw_file, final_file)
        upload_target = final_file
    else:
        upload_target = raw_file

    print(f"\nVideo ready for distribution:")
    print(f" - Path: {upload_target}")
    print(f" - Caption: {caption}")
    print(f" - Tags: {' '.join(tags)}")

    # 3. Publish
    if not dry_run:
        results = publish_to_buffer(upload_target, caption, tags)
        print(f"\n[Completed] Publish results: {results}")
    else:
        print("[Dry Run] Skipped Buffer upload. Video is ready locally.")

def main():
    parser = argparse.ArgumentParser(description="Watermark-Free TikTok Reposter to Buffer")
    parser.add_argument("--url", type=str, help="TikTok video URL to download and repost")
    parser.add_argument("--file", type=str, help="File containing list of TikTok URLs (one per line)")
    parser.add_argument("--video-file", type=str, help="Publish an already-downloaded local video file directly")
    parser.add_argument("--caption", type=str, help="Custom caption / title for the post")
    parser.add_argument("--tags", type=str, default="#inthistown #fyp #viral #shorts", help="Space-separated hashtags")
    parser.add_argument("--no-filter", action="store_true", help="Skip anti-duplicate filter (upload raw video)")
    parser.add_argument("--dry-run", action="store_true", help="Download only, do not publish to Buffer")

    args = parser.parse_args()

    tags = [t.strip() for t in args.tags.split() if t.strip()]

    if args.video_file:
        video_path = Path(args.video_file)
        if not video_path.exists():
            print(f"Error: Video file not found: {video_path}")
            sys.exit(1)
        caption = args.caption or "In this town..."
        print(f"Publishing existing video: {video_path}")
        results = publish_to_buffer(video_path, caption, tags)
        print(f"\n[Completed] Publish results: {results}")
    elif args.url:
        process_url(args.url, caption=args.caption, tags=tags, anti_duplicate=not args.no_filter, dry_run=args.dry_run)
    elif args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Error: URL file not found: {file_path}")
            sys.exit(1)
        with open(file_path, "r") as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        for u in urls:
            process_url(u, caption=args.caption, tags=tags, anti_duplicate=not args.no_filter, dry_run=args.dry_run)
    else:
        print("Please provide --url <TIKTOK_URL> or --file <URLS_FILE>")
        print("Example: python3 repost_tiktok.py --url 'https://www.tiktok.com/@creator/video/123456789' --dry-run")

if __name__ == "__main__":
    main()

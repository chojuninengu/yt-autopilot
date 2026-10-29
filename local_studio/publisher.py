import os
import sys
import subprocess
import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from .config import PROJECT_ROOT, BUFFER_ACCESS_TOKEN, YOUTUBE_TOKEN

# Add project root to sys.path so we can reuse existing tested uploaders
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def upload_to_youtube(video_path: Path, title: str, description: str, tags: list, privacy: str = "public") -> Optional[str]:
    """Uploads video directly to YouTube Shorts via YouTube Data API."""
    try:
        from src.youtube_upload import upload_video, get_credentials
        print(f"[Publisher] Uploading to YouTube: '{title}'...")
        video_id = upload_video(
            video_path=video_path,
            title=title,
            description=description,
            tags=tags,
            privacy_status=privacy
        )
        print(f"[Publisher] Successfully uploaded to YouTube! Video ID: {video_id}")
        print(f"[Publisher] URL: https://youtube.com/shorts/{video_id}")
        return video_id
    except Exception as e:
        print(f"[Publisher] YouTube upload failed: {e}")
        return None

def host_video_for_buffer(video_path: Path) -> Optional[str]:
    """Hosts local video on GitHub Releases so Buffer can fetch and publish it to TikTok."""
    tag = f"v-studio-{datetime.date.today().isoformat()}"
    filename = f"studio_{int(datetime.datetime.now().timestamp())}.mp4"
    staged_file = video_path.parent / filename
    
    # Copy to unique filename
    with open(video_path, "rb") as src, open(staged_file, "wb") as dst:
        dst.write(src.read())

    print(f"[Publisher] Uploading {filename} to GitHub release '{tag}'...")
    try:
        # Check if release exists, if not create it
        check_cmd = ["gh", "release", "view", tag]
        if subprocess.run(check_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode != 0:
            create_cmd = ["gh", "release", "create", tag, str(staged_file), "--title", f"Local Studio Releases {tag}", "--notes", "Automated local studio uploads"]
            subprocess.run(create_cmd, check=True)
        else:
            upload_cmd = ["gh", "release", "upload", tag, str(staged_file), "--clobber"]
            subprocess.run(upload_cmd, check=True)

        public_url = f"https://github.com/chojuninengu/yt-autopilot/releases/download/{tag}/{filename}"
        print(f"[Publisher] Video hosted publicly at: {public_url}")
        return public_url
    except Exception as e:
        print(f"[Publisher] Warning: Failed to host video via gh CLI ({e})")
        return None

def upload_to_tiktok(video_path: Path, caption: str, tags: list) -> Optional[str]:
    """Uploads video to TikTok via Buffer GraphQL API."""
    if not BUFFER_ACCESS_TOKEN:
        print("[Publisher] BUFFER_ACCESS_TOKEN not set, skipping TikTok upload.")
        return None

    public_url = host_video_for_buffer(video_path)
    if not public_url:
        print("[Publisher] Cannot upload to TikTok without public URL.")
        return None

    full_text = f"{caption}\n\n{' '.join(tags)}"
    try:
        from src.buffer_upload import post_video_to_buffer
        print("[Publisher] Dispatching post to Buffer for TikTok...")
        result = post_video_to_buffer(
            video_url=public_url,
            text=full_text,
            service="tiktok",
            share_mode="shareNow",
            dry_run=False
        )
        post_id = result.get("id")
        print(f"[Publisher] Successfully scheduled/sent to TikTok via Buffer! Post ID: {post_id}")
        return post_id
    except Exception as e:
        print(f"[Publisher] TikTok upload failed: {e}")
        return None

def publish_video(video_path: Path, plan: Dict[str, Any], platforms: list = None) -> Dict[str, Any]:
    """Publishes completed video to selected platforms (YouTube, TikTok)."""
    platforms = platforms or ["youtube", "tiktok"]
    title = plan.get("title", "Daily Short")
    caption = plan.get("caption", title)
    tags = plan.get("hashtags", ["#shorts", "#viral"])
    description = f"{caption}\n\n{' '.join(tags)}"

    results = {}
    if "youtube" in platforms:
        results["youtube"] = upload_to_youtube(video_path, title, description, tags)
    if "tiktok" in platforms:
        results["tiktok"] = upload_to_tiktok(video_path, caption, tags)

    return results

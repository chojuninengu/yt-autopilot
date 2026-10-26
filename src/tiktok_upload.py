"""Phase 4b - Upload vertical video to TikTok via Content Posting API v2."""
import json
import os
import pathlib
import time
import requests

ROOT = pathlib.Path(__file__).resolve().parent.parent
INIT_DIRECT_URL = "https://open.tiktokapis.com/v2/post/publish/video/init/"
INIT_DRAFT_URL = "https://open.tiktokapis.com/v2/post/publish/inbox/video/init/"
REFRESH_URL = "https://open.tiktokapis.com/v2/oauth/token/"


def get_tiktok_credentials(token_path: pathlib.Path | None = None) -> dict:
    """Retrieve and refresh TikTok access token."""
    token_file = token_path or ROOT / "tiktok_token.json"
    token_data = None

    # Check environment variable first (for GitHub Actions)
    env_token = os.environ.get("TIKTOK_TOKEN")
    if env_token:
        try:
            token_data = json.loads(env_token)
        except Exception:
            if pathlib.Path(env_token).exists():
                token_data = json.loads(pathlib.Path(env_token).read_text())

    if not token_data and token_file.exists():
        token_data = json.loads(token_file.read_text(encoding="utf-8"))

    if not token_data or "access_token" not in token_data:
        raise RuntimeError(
            "TikTok credentials not found!\n"
            "Run 'python src/auth_tiktok.py' first to link your TikTok account,\n"
            "or set the TIKTOK_TOKEN environment variable."
        )

    # Check expiration and refresh if necessary
    expires_at = token_data.get("expires_at", 0)
    now = time.time()
    if expires_at and now >= expires_at - 300 and "refresh_token" in token_data:
        print("Refreshing TikTok access token...")
        payload = {
            "client_key": token_data.get("client_key"),
            "client_secret": token_data.get("client_secret"),
            "grant_type": "refresh_token",
            "refresh_token": token_data["refresh_token"]
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        r = requests.post(REFRESH_URL, data=payload, headers=headers, timeout=30)
        r.raise_for_status()
        new_data = r.json().get("data", {})
        if "access_token" in new_data:
            token_data["access_token"] = new_data["access_token"]
            token_data["refresh_token"] = new_data.get("refresh_token", token_data["refresh_token"])
            token_data["expires_at"] = int(now) + new_data.get("expires_in", 86400)
            if token_file.exists():
                token_file.write_text(json.dumps(token_data, indent=2), encoding="utf-8")

    return token_data


def upload_tiktok_video(
    video_path: pathlib.Path,
    caption: str,
    hashtags: list[str],
    post_mode: str = "DIRECT_POST",  # or "MEDIA_UPLOAD" for Drafts
    privacy_level: str = "PUBLIC_TO_EVERYONE"  # or "SELF_ONLY", "MUTUAL_FOLLOW_FRIENDS"
) -> str:
    """Initialize upload and push video chunks to TikTok."""
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    creds = get_tiktok_credentials()
    access_token = creds["access_token"]

    full_title = f"{caption} " + " ".join("#" + h.lstrip("#") for h in hashtags)
    full_title = full_title[:2200]  # TikTok caption limit

    video_size = video_path.stat().st_size
    chunk_size = video_size  # single chunk upload for short videos < 50MB
    total_chunk_count = 1

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json; charset=UTF-8"
    }

    if post_mode == "MEDIA_UPLOAD":
        init_url = INIT_DRAFT_URL
        body = {
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": video_size,
                "chunk_size": chunk_size,
                "total_chunk_count": total_chunk_count
            }
        }
    else:
        init_url = INIT_DIRECT_URL
        body = {
            "post_info": {
                "title": full_title,
                "privacy_level": privacy_level,
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
                "video_cover_timestamp_ms": 1000
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": video_size,
                "chunk_size": chunk_size,
                "total_chunk_count": total_chunk_count
            }
        }

    print(f"Initializing TikTok video upload ({post_mode})...")
    resp = requests.post(init_url, headers=headers, json=body, timeout=30)
    resp.raise_for_status()
    resp_json = resp.json()

    error_info = resp_json.get("error", {})
    if error_info.get("code") != "ok":
        raise RuntimeError(f"TikTok upload init failed: {error_info.get('message')}")

    data = resp_json.get("data", {})
    publish_id = data.get("publish_id")
    upload_url = data.get("upload_url")

    if not upload_url:
        raise RuntimeError(f"No upload URL returned from TikTok: {resp_json}")

    print(f"Uploading video file ({video_size / (1024*1024):.2f} MB) to TikTok...")
    upload_headers = {
        "Content-Type": "video/mp4",
        "Content-Range": f"bytes 0-{video_size - 1}/{video_size}"
    }

    with open(video_path, "rb") as f_in:
        put_resp = requests.put(upload_url, headers=upload_headers, data=f_in, timeout=120)
        put_resp.raise_for_status()

    print(f"Upload completed successfully! Publish ID: {publish_id}")
    return publish_id

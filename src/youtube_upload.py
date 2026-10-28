"""Phase 3 - Upload vertical short video to YouTube via YouTube Data API v3."""
import json
import os
import pathlib
import time
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

ROOT = pathlib.Path(__file__).resolve().parent.parent


def get_credentials(token_path: pathlib.Path | None = None) -> Credentials:
    """Retrieve and refresh YouTube OAuth2 credentials."""
    creds = None
    token_file = token_path or ROOT / "youtube_token.json"

    # Check environment variable first (for GitHub Actions)
    env_token = os.environ.get("YOUTUBE_TOKEN")
    if env_token:
        raw = env_token.strip()
        # Handle cases where env_token was wrapped in quotes
        if (raw.startswith("'") and raw.endswith("'")) or (raw.startswith('"') and raw.endswith('"')):
            try:
                unquoted = json.loads(raw)
                if isinstance(unquoted, (str, dict)):
                    raw = unquoted
            except Exception:
                raw = raw[1:-1].strip()

        token_data = None
        if isinstance(raw, dict):
            token_data = raw
        elif isinstance(raw, str):
            try:
                token_data = json.loads(raw)
            except Exception as ex_json:
                # Try base64
                try:
                    import base64
                    decoded = base64.b64decode(raw).decode("utf-8")
                    token_data = json.loads(decoded)
                except Exception:
                    token_data = None
                    print(f"Warning: Failed to parse YOUTUBE_TOKEN as JSON: {ex_json}")

        if token_data and isinstance(token_data, dict):
            if "installed" in token_data or "web" in token_data:
                raise RuntimeError(
                    "YOUTUBE_TOKEN appears to be client_secrets.json instead of youtube_token.json!\n"
                    "Run 'python src/auth_youtube.py' first and copy the resulting youtube_token.json into YOUTUBE_TOKEN."
                )
            try:
                creds = Credentials.from_authorized_user_info(token_data)
            except Exception as ex_init:
                print(f"Warning: Failed to create Credentials from YOUTUBE_TOKEN: {ex_init}")
        elif isinstance(raw, str) and pathlib.Path(raw).exists():
            creds = Credentials.from_authorized_user_file(raw)

    # Check local token file
    if not creds and token_file.exists():
        creds = Credentials.from_authorized_user_file(str(token_file))

    if not creds:
        raise RuntimeError(
            "YouTube credentials not found!\n"
            "Run 'python src/auth_youtube.py' first to link your YouTube channel,\n"
            "or set the YOUTUBE_TOKEN environment variable."
        )

    if not creds.valid:
        if creds.refresh_token:
            print("Refreshing expired YouTube OAuth access token...")
            creds.refresh(Request())
            if token_file.exists():
                token_dict = {
                    "token": creds.token,
                    "refresh_token": creds.refresh_token,
                    "token_uri": creds.token_uri,
                    "client_id": creds.client_id,
                    "client_secret": creds.client_secret,
                    "scopes": creds.scopes
                }
                token_file.write_text(json.dumps(token_dict, indent=2))
        else:
            print("Warning: YouTube credentials are not valid and no refresh_token is present.")

    return creds


def upload_video(
    video_path: pathlib.Path,
    title: str,
    description: str,
    tags: list[str],
    privacy_status: str = "private",
    category_id: str = "28"  # Science & Technology
) -> str:
    """Upload video to YouTube with resumable chunked upload."""
    if not video_path.exists():
        raise FileNotFoundError(f"Video file does not exist: {video_path}")

    # Ensure title has #shorts and respects 100 character YouTube limit
    if "#shorts" not in title.lower():
        title = f"{title.strip()} #shorts"
    title = title[:100]

    creds = get_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags[:15],
            "categoryId": category_id
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False
        }
    }

    media = MediaFileUpload(
        str(video_path),
        mimetype="video/mp4",
        chunksize=1024 * 1024 * 4,  # 4MB chunks
        resumable=True
    )

    request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=media
    )

    print(f"Uploading '{title}' to YouTube ({privacy_status})...")
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            percent = int(status.progress() * 100)
            print(f"Upload progress: {percent}%")

    video_id = response.get("id")
    video_url = f"https://youtu.be/{video_id}"
    print(f"Upload complete! Video URL: {video_url}")
    return video_id

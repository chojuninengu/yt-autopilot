"""Buffer API uploader for publishing videos to TikTok via Buffer GraphQL API."""
import argparse
import datetime
import json
import os
import pathlib
import sys
import requests

try:
    from dotenv import load_dotenv
    _env_path = pathlib.Path(__file__).resolve().parent.parent / ".env"
    if _env_path.exists():
        load_dotenv(dotenv_path=_env_path)
except ImportError:
    pass

ROOT = pathlib.Path(__file__).resolve().parent.parent
BUFFER_API_URL = "https://api.buffer.com"


def get_buffer_token() -> str:
    token = os.environ.get("BUFFER_ACCESS_TOKEN")
    if not token:
        raise RuntimeError("BUFFER_ACCESS_TOKEN is not set in environment or .env file.")
    return token.strip()


def execute_graphql(query: str, variables: dict | None = None) -> dict:
    token = get_buffer_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    resp = requests.post(BUFFER_API_URL, headers=headers, json=payload, timeout=20)
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data and data["errors"]:
        raise RuntimeError(f"Buffer GraphQL error: {data['errors']}")
    return data.get("data", {})


def get_channels() -> list[dict]:
    """Retrieve connected social media channels from Buffer."""
    # First get organization ID
    account_data = execute_graphql("""
        query GetAccount {
          account {
            id
            organizations {
              id
              name
            }
          }
        }
    """)
    orgs = account_data.get("account", {}).get("organizations", [])
    if not orgs:
        raise RuntimeError("No Buffer organization found for this account.")
    org_id = orgs[0]["id"]

    # Query channels for organization
    channels_data = execute_graphql("""
        query GetChannels($orgId: OrganizationId!) {
          channels(input: {organizationId: $orgId}) {
            id
            name
            service
            displayName
          }
        }
    """, {"orgId": org_id})
    return channels_data.get("channels", [])


def post_video_to_buffer(
    video_url: str,
    text: str,
    service: str = "tiktok",
    share_mode: str = "shareNow",
    dry_run: bool = False
) -> dict:
    """Post video to Buffer channel (e.g. TikTok) using a direct publicly accessible MP4 URL."""
    channels = get_channels()
    target_channel = None
    for ch in channels:
        if ch.get("service", "").lower() == service.lower():
            target_channel = ch
            break

    if not target_channel:
        available = [f"{c.get('service')} ({c.get('name')})" for c in channels]
        raise RuntimeError(f"No channel found for service '{service}'. Available channels: {available}")

    channel_id = target_channel["id"]
    channel_name = target_channel.get("name") or target_channel.get("displayName")
    print(f"Target Buffer channel: {channel_name} (Service: {service}, ID: {channel_id})")
    print(f"Video URL: {video_url}")
    print(f"Caption: {text[:100]}...")

    if dry_run:
        print("Dry run enabled: Skipping actual Buffer GraphQL mutation.")
        return {"dry_run": True, "channel_id": channel_id, "service": service}

    mutation = """
    mutation CreatePost($input: CreatePostInput!) {
      createPost(input: $input) {
        ... on PostActionSuccess {
          post {
            id
            status
            dueAt
          }
        }
        ... on InvalidInputError {
          message
        }
        ... on UnexpectedError {
          message
        }
        ... on LimitReachedError {
          message
        }
      }
    }
    """

    variables = {
      "input": {
        "channelId": channel_id,
        "text": text,
        "mode": share_mode,
        "schedulingType": "automatic",
        "needsApproval": False,
        "assets": [
          {
            "video": {
              "url": video_url
            }
          }
        ]
      }
    }

    result = execute_graphql(mutation, variables)
    create_post_result = result.get("createPost", {})
    if "message" in create_post_result:
        raise RuntimeError(f"Buffer API error: {create_post_result['message']}")

    post_info = create_post_result.get("post", {})
    post_id = post_info.get("id")
    print(f"Successfully posted video to Buffer {service.upper()}! Post ID: {post_id}")
    return post_info


def parse_args():
    parser = argparse.ArgumentParser(description="Upload video to TikTok via Buffer GraphQL API.")
    parser.add_argument("--plan", type=str, default=None, help="Path to plan JSON file.")
    parser.add_argument("--video-url", type=str, default=None, help="Direct public URL to MP4 file.")
    parser.add_argument("--service", type=str, default="tiktok", choices=["tiktok", "youtube"], help="Target platform in Buffer.")
    parser.add_argument("--mode", type=str, default="shareNow", choices=["shareNow", "addToQueue"], help="Buffer share mode.")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without posting.")
    return parser.parse_args()


def resolve_plan_path(custom_plan: str | None, out_dir: pathlib.Path) -> pathlib.Path:
    if custom_plan:
        return pathlib.Path(custom_plan)

    run_id = os.environ.get("RUN_ID")
    if run_id:
        p = out_dir / f"{run_id}-plan.json"
        if p.exists():
            return p

    candidates = [p for p in out_dir.glob("*-plan.json") if p.name != "latest-plan.json"]
    if candidates:
        candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return candidates[0]

    latest = out_dir / "latest-plan.json"
    if latest.exists():
        return latest

    today = datetime.date.today().isoformat()
    return out_dir / f"{today}-plan.json"


def main():
    args = parse_args()
    out_dir = ROOT / "output"

    plan_path = resolve_plan_path(args.plan, out_dir)
    if not plan_path.exists():
        sys.exit(f"Plan file not found: {plan_path}")

    plan = json.loads(plan_path.read_text(encoding="utf-8"))

    # Caption and hashtags from plan
    tt_meta = plan.get("tiktok", {})
    caption = tt_meta.get("caption", plan.get("video_title", "Daily Video"))
    hashtags = " ".join("#" + h.lstrip("#") for h in tt_meta.get("hashtags", ["shorts", "trending"]))
    full_text = f"{caption}\n\n{hashtags}".strip()

    # Determine video URL
    video_url = args.video_url
    if not video_url:
        prefix = plan_path.stem.replace("-plan", "") if "-plan" in plan_path.stem else datetime.date.today().isoformat()
        video_url = f"https://github.com/chojuninengu/yt-autopilot/releases/download/v{prefix}/{prefix}-video.mp4"

    try:
        post_video_to_buffer(
            video_url=video_url,
            text=full_text,
            service=args.service,
            share_mode=args.mode,
            dry_run=args.dry_run
        )
    except Exception as ex:
        sys.exit(f"Buffer posting failed: {ex}")


if __name__ == "__main__":
    main()

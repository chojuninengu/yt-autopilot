"""Phase 3 entry point: read plan + video -> upload to YouTube."""
import argparse
import datetime
import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from youtube_upload import upload_video  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent


def parse_args():
    parser = argparse.ArgumentParser(description="Upload rendered vertical video to YouTube.")
    parser.add_argument(
        "--plan", type=str, default=None,
        help="Path to plan JSON (defaults to today's plan in output/)."
    )
    parser.add_argument(
        "--video", type=str, default=None,
        help="Path to video MP4 (defaults to today's video in output/)."
    )
    parser.add_argument(
        "--privacy", type=str, default=None, choices=["private", "unlisted", "public"],
        help="Privacy status on YouTube (defaults to config.json or 'public')."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Simulate upload and inspect metadata without calling YouTube API."
    )
    return parser.parse_args()


def resolve_paths(custom_plan: str | None, custom_video: str | None, out_dir: pathlib.Path):
    if custom_plan:
        plan_path = pathlib.Path(custom_plan)
    else:
        run_id = os.environ.get("RUN_ID")
        if run_id and (out_dir / f"{run_id}-plan.json").exists():
            plan_path = out_dir / f"{run_id}-plan.json"
        else:
            candidates = [p for p in out_dir.glob("*-plan.json") if p.name != "latest-plan.json"]
            if candidates:
                candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                plan_path = candidates[0]
            elif (out_dir / "latest-plan.json").exists():
                plan_path = out_dir / "latest-plan.json"
            else:
                today = datetime.date.today().isoformat()
                plan_path = out_dir / f"{today}-plan.json"

    if custom_video:
        video_path = pathlib.Path(custom_video)
    else:
        # Match the plan prefix if possible
        if plan_path.name.endswith("-plan.json") and plan_path.name != "latest-plan.json":
            prefix = plan_path.name.replace("-plan.json", "")
            video_path = out_dir / f"{prefix}-video.mp4"
        else:
            candidates = sorted(out_dir.glob("*-video.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
            if candidates:
                video_path = candidates[0]
            else:
                today = datetime.date.today().isoformat()
                video_path = out_dir / f"{today}-video.mp4"

    return plan_path, video_path


def main():
    args = parse_args()
    out_dir = ROOT / "output"

    plan_path, video_path = resolve_paths(args.plan, args.video, out_dir)

    if not plan_path.exists():
        sys.exit(f"Plan file not found: {plan_path}. Run Phase 1 first.")
    if not video_path.exists():
        sys.exit(f"Video file not found: {video_path}. Run Phase 2 first.")

    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    yt_meta = plan.get("youtube", {})

    title = yt_meta.get("title", plan.get("video_title", "Daily Video"))
    description = f"{yt_meta.get('description', '')}\n\n" + " ".join(
        "#" + h.lstrip("#") for h in yt_meta.get("hashtags", ["shorts", "trending"])
    )
    tags = yt_meta.get("hashtags", ["shorts", "trending"])

    cfg_path = ROOT / "config.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.exists() else {}
    privacy = args.privacy or cfg.get("youtube_privacy", "public")

    if cfg.get("disclose_ai_in_description", True) and "Visuals generated with AI" not in description:
        description += "\n\nVisuals generated with AI."

    if args.dry_run:
        print("=== DRY RUN: YouTube Upload Preview ===")
        print(f"Video File:  {video_path} ({video_path.stat().st_size / (1024*1024):.2f} MB)")
        print(f"Title:       {title}")
        print(f"Privacy:     {privacy}")
        print(f"Tags:        {tags}")
        print(f"Description:\n{description}")
        print("Dry run completed successfully (no video was uploaded).")
        return

    try:
        video_id = upload_video(
            video_path=video_path,
            title=title,
            description=description,
            tags=tags,
            privacy_status=privacy
        )
        print(f"\nPhase 3 Complete! Video is live at https://youtu.be/{video_id} ({privacy})")
    except Exception as ex:
        sys.exit(f"Upload failed: {ex}")


if __name__ == "__main__":
    main()

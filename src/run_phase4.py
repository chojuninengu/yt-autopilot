"""Phase 4 entry point: read plan + video -> upload to TikTok."""
import argparse
import datetime
import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from tiktok_upload import upload_tiktok_video  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent


def parse_args():
    parser = argparse.ArgumentParser(description="Upload rendered vertical video to TikTok.")
    parser.add_argument(
        "--plan", type=str, default=None,
        help="Path to plan JSON (defaults to today's plan in output/)."
    )
    parser.add_argument(
        "--video", type=str, default=None,
        help="Path to video MP4 (defaults to today's video in output/)."
    )
    parser.add_argument(
        "--mode", type=str, default="MEDIA_UPLOAD", choices=["MEDIA_UPLOAD", "DIRECT_POST"],
        help="Upload mode: 'MEDIA_UPLOAD' uploads to Creator Drafts (recommended); 'DIRECT_POST' publishes directly."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Simulate TikTok upload and inspect caption and tags without uploading."
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
    tt_meta = plan.get("tiktok", {})

    caption = tt_meta.get("caption", plan.get("video_title", "Daily Video"))
    hashtags = tt_meta.get("hashtags", ["fyp", "trending", "viral"])

    cfg_path = ROOT / "config.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.exists() else {}
    if cfg.get("disclose_ai_in_description", True) and "Visuals generated with AI" not in caption:
        caption += " (Visuals generated with AI.)"

    if args.dry_run:
        print("=== DRY RUN: TikTok Upload Preview ===")
        print(f"Video File: {video_path} ({video_path.stat().st_size / (1024*1024):.2f} MB)")
        print(f"Mode:       {args.mode}")
        print(f"Caption:    {caption}")
        print(f"Hashtags:   {hashtags}")
        print("Dry run completed successfully (no video was uploaded).")
        return

    try:
        publish_id = upload_tiktok_video(
            video_path=video_path,
            caption=caption,
            hashtags=hashtags,
            post_mode=args.mode
        )
        if args.mode == "MEDIA_UPLOAD":
            print(f"\nPhase 4 Complete! Video uploaded to TikTok Creator Drafts (Publish ID: {publish_id}).")
            print("Check your TikTok mobile app notification to review and publish!")
        else:
            print(f"\nPhase 4 Complete! Video directly posted to TikTok (Publish ID: {publish_id}).")
    except Exception as ex:
        sys.exit(f"TikTok upload failed: {ex}")


if __name__ == "__main__":
    main()

"""Phase 2 entry point: read plan -> synthesize voice -> fetch footage -> render video."""
import argparse
import datetime
import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from render import render_video  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent


def parse_args():
    parser = argparse.ArgumentParser(description="Render a complete vertical short-form video from a plan.")
    parser.add_argument(
        "--plan", type=str, default=None,
        help="Path to the plan JSON file (defaults to today's plan in output/)."
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Custom output MP4 path (defaults to output/YYYY-MM-DD-video.mp4)."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Run rendering in dry-run test mode without external image generation calls."
    )
    return parser.parse_args()


def resolve_plan_path(custom_plan: str | None, out_dir: pathlib.Path) -> pathlib.Path:
    if custom_plan:
        return pathlib.Path(custom_plan)

    run_id = os.environ.get("RUN_ID")
    if run_id:
        p = out_dir / f"{run_id}-plan.json"
        if p.exists():
            return p

    # Find the newest plan file in output/
    candidates = [
        p for p in out_dir.glob("*-plan.json")
        if p.name != "latest-plan.json"
    ]
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
    out_dir.mkdir(exist_ok=True)

    plan_path = resolve_plan_path(args.plan, out_dir)
    if not plan_path.exists():
        sys.exit(
            f"Plan file not found: {plan_path}\n"
            "Run Phase 1 first to create a plan:\n"
            "  python src/run_phase1.py"
        )

    print(f"Loading plan from: {plan_path}")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))

    cfg_path = ROOT / "config.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8")) if cfg_path.exists() else {}
    if args.dry_run:
        cfg["dry_run"] = True

    if args.output:
        output_path = pathlib.Path(args.output)
    else:
        if plan_path.name.endswith("-plan.json") and plan_path.name != "latest-plan.json":
            prefix = plan_path.name.replace("-plan.json", "")
            output_path = out_dir / f"{prefix}-video.mp4"
        else:
            today = datetime.date.today().isoformat()
            output_path = out_dir / f"{today}-video.mp4"

    print(f"Rendering video: '{plan.get('video_title', 'Video')}'...")
    render_video(plan, output_path, cfg=cfg)

    # Persist provider information back to plan JSON
    plan_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Updated plan with provider records: {plan_path}")

    print(f"\nPhase 2 Complete!")
    print(f"Generated video: {output_path}")
    print(f"File size: {output_path.stat().st_size / (1024 * 1024):.2f} MB")


if __name__ == "__main__":
    main()

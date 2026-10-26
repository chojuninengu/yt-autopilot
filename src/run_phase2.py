"""Phase 2 entry point: read plan -> synthesize voice -> fetch footage -> render video."""
import argparse
import datetime
import json
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
    return parser.parse_args()


def main():
    args = parse_args()
    today = datetime.date.today().isoformat()
    out_dir = ROOT / "output"
    out_dir.mkdir(exist_ok=True)

    plan_path = pathlib.Path(args.plan) if args.plan else out_dir / f"{today}-plan.json"
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

    output_path = pathlib.Path(args.output) if args.output else out_dir / f"{today}-video.mp4"
    print(f"Rendering video: '{plan.get('video_title', 'Video')}'...")
    render_video(plan, output_path, cfg=cfg)

    print(f"\nPhase 2 Complete!")
    print(f"Generated video: {output_path}")
    print(f"File size: {output_path.stat().st_size / (1024 * 1024):.2f} MB")


if __name__ == "__main__":
    main()

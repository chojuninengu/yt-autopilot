"""Phase 1 entry point: scout trends -> plan an original video -> save to output/."""
import argparse
import datetime
import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from scout import collect      # noqa: E402
from ideate import ideate      # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent


def parse_args():
    parser = argparse.ArgumentParser(description="Scout trends and generate short-form video plans.")
    parser.add_argument(
        "--dry-run", "--mock", action="store_true", dest="mock",
        help="Run pipeline locally with mock ideation (does not require GEMINI_API_KEY)."
    )
    parser.add_argument(
        "--scout-only", action="store_true",
        help="Only run trend collection and save trends to output/."
    )
    parser.add_argument(
        "--run-id", type=str, default=None,
        help="Custom run ID prefix (defaults to RUN_ID env var or UTC timestamp YYYY-MM-DD_HHMM)."
    )
    return parser.parse_args()


def main():
    args = parse_args()
    cfg = json.loads((ROOT / "config.json").read_text())
    run_id = args.run_id or os.environ.get("RUN_ID") or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d_%H%M")
    out_dir = ROOT / "output"
    out_dir.mkdir(exist_ok=True)

    print(f"Starting Phase 1 (Run ID: {run_id})...")
    print("Scouting trends across sources...")
    items, errors = collect(cfg)
    print(f"Collected {len(items)} items; source errors: {errors or 'none'}")
    trends_file = out_dir / f"{run_id}-trends.json"
    trends_file.write_text(
        json.dumps({"items": items, "errors": errors}, indent=2, ensure_ascii=False)
    )
    print(f"Saved trends to {trends_file}")

    if not items:
        sys.exit("No trend data from any source - nothing to plan.")

    if args.scout_only:
        print("Scout-only mode completed successfully.")
        return

    if args.mock:
        print("Running in dry-run mode (using mock ideation)...")

    try:
        plan = ideate(items, cfg, mock=args.mock)
    except Exception as ex:
        sys.exit(f"Error during ideation: {ex}")

    if cfg.get("disclose_ai_in_description", True):
        ai_notice = "Visuals generated with AI."
        yt_desc = plan.get("youtube", {}).get("description", "")
        if ai_notice not in yt_desc:
            plan["youtube"]["description"] = (yt_desc + f"\n\n{ai_notice}").strip()
        tt_cap = plan.get("tiktok", {}).get("caption", "")
        if ai_notice not in tt_cap:
            plan["tiktok"]["caption"] = (tt_cap + f" ({ai_notice})").strip()

    plan_json_file = out_dir / f"{run_id}-plan.json"
    plan_json_file.write_text(json.dumps(plan, indent=2, ensure_ascii=False))

    md = [
        f"# {plan['video_title']}", "",
        f"**Trend:** {plan['picked_trend']}", "",
        f"**Why it's viral:** {plan['why_viral']}", "",
        f"**Core idea:** {plan['core_idea']}", "",
        "## Script", plan["script"], "",
        "## Scenes"
    ]
    for i, s in enumerate(plan["scenes"], 1):
        md.append(f"{i}. {s['narration']}  \n   _visuals: {', '.join(s['visual_keywords'])}_")
    md += [
        "", "## YouTube", plan["youtube"]["title"], "", plan["youtube"]["description"], "",
        " ".join("#" + h.lstrip("#") for h in plan["youtube"]["hashtags"]),
        "", "## TikTok", plan["tiktok"]["caption"], "",
        " ".join("#" + h.lstrip("#") for h in plan["tiktok"]["hashtags"])
    ]
    plan_md_file = out_dir / f"{run_id}-plan.md"
    plan_md_file.write_text("\n".join(md))

    # Also write latest-plan convenience copy
    (out_dir / "latest-plan.json").write_text(json.dumps(plan, indent=2, ensure_ascii=False))
    (out_dir / "latest-plan.md").write_text("\n".join(md))

    print(f"Saved plan to {plan_json_file} and {plan_md_file}")
    print("Done:", plan["video_title"])


if __name__ == "__main__":
    main()

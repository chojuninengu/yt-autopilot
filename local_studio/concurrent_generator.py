"""
local_studio/concurrent_generator.py
====================================
Simultaneously generates multiple 3D animated character fables and stories in parallel.
Uses ThreadPoolExecutor to run scripting, audio synthesis, Agnes 3D visual generation,
and video assembly concurrently across CPU threads.
"""

import sys
import time
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from local_studio.main import run_fable_video


STORIES = [
    {
        "id": 1,
        "topic": (
            "A lion cub who grew up in a flock of sheep, bleating and grazing timidly like a sheep without knowing his true royal origin. "
            "When a vicious wolf attacks the herd, he catches his reflection in the water, awakens his kingly identity, "
            "and lets out a thunderous roar that shakes the valley and protects the flock."
        )
    },
    {
        "id": 2,
        "topic": (
            "A gentle and brave black goat who is bullied, excluded, and mocked by a herd of proud white goats because of his dark coat (racism and prejudice). "
            "When a dangerous blizzard and mountain predator strikes the herd, the black goat demonstrates supreme courage and strength, "
            "saving all the white goats and humbling their pride with a powerful lesson on dignity and true worth."
        )
    },
    {
        "id": 3,
        "topic": (
            "A black Africa evolution and spiritual awakening through the gospel of Christ Jesus: "
            "from ancient trials and spiritual bondage to rising in unshakeable faith, vibrant joyful worship, healing, unity, "
            "and divine light, transforming villages and nations through the love, sacrifice, and redemption of Jesus Christ."
        )
    }
]


def generate_single_story(story_cfg: dict, total: int, publish: bool = True, platforms: list = None):
    index = story_cfg["id"]
    topic = story_cfg["topic"]
    print(f"\n[Worker {index}] >>> STARTING simultaneous video generation for: '{topic[:45]}...'")
    start = time.time()
    try:
        success = run_fable_video(
            index=index,
            total=total,
            topic=topic,
            publish=publish,
            platforms=platforms or ["youtube", "tiktok"]
        )
        duration = time.time() - start
        return {
            "id": index,
            "topic": topic,
            "success": success,
            "duration": duration
        }
    except Exception as e:
        print(f"\n[Worker {index}] ❌ Exception during generation: {e}")
        return {
            "id": index,
            "topic": topic,
            "success": False,
            "error": str(e),
            "duration": time.time() - start
        }


def main():
    parser = argparse.ArgumentParser(description="Simultaneously generate 3 AI videos using Local Studio.")
    parser.add_argument("--no-publish", action="store_true", help="Generate videos locally without publishing")
    parser.add_argument("--platforms", type=str, default="youtube,tiktok", help="Comma-separated platforms: youtube,tiktok")
    args = parser.parse_args()

    selected_platforms = [p.strip().lower() for p in args.platforms.split(",") if p.strip()]
    publish = not args.no_publish

    print("\n" + "="*70)
    print("🚀 LOCAL STUDIO: CONCURRENT MULTI-VIDEO GENERATOR")
    print(f"🎬 Generating {len(STORIES)} 3D AI Videos SIMULTANEOUSLY")
    for s in STORIES:
        print(f"  [{s['id']}] {s['topic'][:75]}...")
    print(f"🌐 Publishing: {'Active (' + ','.join(selected_platforms) + ')' if publish else 'Disabled (Local only)'}")
    print("="*70 + "\n")

    overall_start = time.time()
    results = []

    with ThreadPoolExecutor(max_workers=len(STORIES)) as executor:
        futures = {
            executor.submit(
                generate_single_story,
                story,
                len(STORIES),
                publish=publish,
                platforms=selected_platforms
            ): story["id"]
            for story in STORIES
        }

        for future in as_completed(futures):
            story_id = futures[future]
            try:
                res = future.result()
                results.append(res)
                print(f"\n[Main] 🎉 Finished Video [{story_id}] in {res['duration']:.1f}s (Success: {res['success']})")
            except Exception as e:
                print(f"\n[Main] ❌ Future failed for Video [{story_id}]: {e}")

    total_time = time.time() - overall_start
    print("\n" + "="*70)
    print(f"🏁 ALL {len(STORIES)} SIMULTANEOUS RUNS COMPLETED in {total_time:.1f}s ({total_time/60:.1f}m)")
    for r in sorted(results, key=lambda x: x["id"]):
        status = "✅ SUCCESS" if r.get("success") else "❌ FAILED"
        print(f"  • Video {r['id']}: {status} ({r.get('duration', 0):.1f}s) - {r['topic'][:60]}...")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()

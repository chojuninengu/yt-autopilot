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
            "The Hamster Who Built an Iron Mech Suit. "
            "Pip, an energetic, squeaky baby hamster genius (excited child voice), gets tired of being intimidated by Barnaby, "
            "the lazy aristocratic house cat (deep haughty male voice). Pip builds a miniature steampunk mech suit powered by sunflower seeds "
            "and stomps into the living room to formally renegotiate cheese rations."
        )
    },
    {
        "id": 2,
        "topic": (
            "The Grandma Who Taught a Frost Dragon to Knit. "
            "Nonna Gladys, a feisty 80-year-old grandmother with thick spectacles (warm expressive elderly woman voice), "
            "discovers a shivering, sneezing baby frost dragon named Blizzard (trembling young child voice) on her snowy porch. "
            "Instead of screaming, she sits him by the fireplace and firmly insists on knitting him a massive wool scarf before he catches a cold."
        )
    },
    {
        "id": 3,
        "topic": (
            "The Street Pigeon Who Became an Art Critic. "
            "Pierre, a cultured city pigeon wearing a tiny monocle (flamboyant theatrical French male voice), "
            "wanders into the Grand Museum and starts passionately critiquing modern sculptures to an astonished museum curator named Sophie "
            "(curious sophisticated female voice), who realizes the bird actually has better taste than the board of directors."
        )
    },
    {
        "id": 4,
        "topic": (
            "The Golden Retriever Who Discovered He Speaks French. "
            "Barnaby, a goofball golden retriever (bubbly enthusiastic boy voice), accidentally eats a magical butter croissant "
            "and suddenly starts speaking elegant philosophy in fluent French. He politely questions his bewildered human owner, Emily "
            "(sweet amazed woman voice), about the existential meaning of the tennis ball."
        )
    },
    {
        "id": 5,
        "topic": (
            "The Little Girl and the Grumpy Cloud. "
            "Maya, a sweet 6-year-old girl with a bright red raincoat (gentle innocent child voice), "
            "notices a gloomy, grumpy thundercloud named Nimbus (cranky rumbling elder voice) hovering specifically over her treehouse. "
            "Rather than running away, she offers Nimbus a freshly baked chocolate chip cookie, turning his lightning bolts into sparkling rainbow confetti."
        )
    },
    {
        "id": 6,
        "topic": (
            "The Squirrel Secret Agent and the Giant Acorn. "
            "Agent Chestnut, a dashing squirrel secret agent in a miniature tuxedo (intense cinematic action hero male voice), "
            "infiltrates the top canopy of the ancient Oak fortress to retrieve the legendary Golden Acorn from Professor Hoot, "
            "a grumpy scholarly owl librarian (pompous academic elder voice)."
        )
    },
    {
        "id": 7,
        "topic": (
            "The Cat Who Realized He's Living in an RPG. "
            "Jasper, a dramatic ginger cat (dramatic heroic male voice), wakes up to discover visible holographic quest markers "
            "and HP bars floating above his human owner, Claire (cheerful everyday female voice). Convinced he must level up to save the realm, "
            "Jasper embarks on an epic quest to slay the vacuum cleaner."
        )
    },
    {
        "id": 8,
        "topic": (
            "The Baby Polar Bear and the Sunbeam. "
            "Koda, a curious fluffy baby polar bear (tender adventurous child voice), chases an elusive golden beam of Arctic sunlight "
            "across shimmering glaciers, bumping into Barnaby, an ancient singing walrus (booming jolly grandfather voice), "
            "who reveals the secret to keeping warmth in your heart through winter."
        )
    },
    {
        "id": 9,
        "topic": (
            "The Tough Detective Questioned by a Sassy Parrot. "
            "Detective Jack Vance, a cynical 1940s film noir detective in a trench coat (gravelly hard-boiled male voice), "
            "investigates a missing bakery heist, only to find himself completely outsmarted and cross-examined by Captain Polly, "
            "an ultra-sassy, fast-talking cockatoo (witty sharp female voice)."
        )
    },
    {
        "id": 10,
        "topic": (
            "The Tiny Robot Looking for the Reset Button. "
            "Widget, a curious little brass clockwork robot with glowing blue eyes (wonder-filled soft child voice), "
            "wanders into an enchanted mossy forest searching for the Universe's factory reset button. He meets Elder Oogway, "
            "a giant 500-year-old forest tortoise (deep peaceful ancient voice), who teaches him why life is only meaningful because every second can only happen once."
        )
    }
]


def generate_single_story(story_cfg: dict, total: int, publish: bool = True, platforms: list = None):
    index = story_cfg["id"]
    topic = story_cfg["topic"]
    print(f"\n[Worker {index}] >>> STARTING video generation for: '{topic[:55]}...'")
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
    parser = argparse.ArgumentParser(description="Batch generate 3D AI videos using Local Studio.")
    parser.add_argument("--count", type=int, default=10, help="Number of videos to generate (up to 10)")
    parser.add_argument("--workers", type=int, default=2, help="Number of concurrent generation threads")
    parser.add_argument("--no-publish", action="store_true", help="Generate videos locally without publishing")
    parser.add_argument("--platforms", type=str, default="youtube,tiktok", help="Comma-separated platforms: youtube,tiktok")
    args = parser.parse_args()

    selected_platforms = [p.strip().lower() for p in args.platforms.split(",") if p.strip()]
    publish = not args.no_publish
    active_stories = STORIES[:max(1, min(args.count, len(STORIES)))]

    print("\n" + "="*70)
    print("🚀 LOCAL STUDIO: CONCURRENT MULTI-VIDEO BATCH PRODUCER")
    print(f"🎬 Producing {len(active_stories)} 3D AI Videos (Workers: {args.workers})")
    for s in active_stories:
        print(f"  [{s['id']:2d}] {s['topic'][:75]}...")
    print(f"🌐 Publishing: {'Active (' + ','.join(selected_platforms) + ')' if publish else 'Disabled (Local only)'}")
    print("="*70 + "\n")

    overall_start = time.time()
    results = []

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(
                generate_single_story,
                story,
                len(active_stories),
                publish=publish,
                platforms=selected_platforms
            ): story["id"]
            for story in active_stories
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
    print(f"🏁 ALL {len(active_stories)} BATCH RUNS COMPLETED in {total_time:.1f}s ({total_time/60:.1f}m)")
    for r in sorted(results, key=lambda x: x["id"]):
        status = "✅ SUCCESS" if r.get("success") else "❌ FAILED"
        print(f"  • Video {r['id']:2d}: {status} ({r.get('duration', 0):.1f}s) - {r['topic'][:60]}...")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()

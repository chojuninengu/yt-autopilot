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
            "The 60-Year Umbrella Promise. "
            "Arthur (gentle, warm elderly husband voice) and Evelyn (sweet, frail elderly wife voice) have been married 60 years. "
            "In a rainy London park, Arthur still holds an oversized red umbrella solely over Evelyn, getting soaked himself just as he did on their very first date in 1964. "
            "Evelyn softly touches his cheek and asks why he never bought a bigger umbrella, and Arthur smiles: 'Because then you wouldn't hold my arm so close.'"
        )
    },
    {
        "id": 2,
        "topic": (
            "The Robot Who Learned What 'I Do' Means. "
            "Orion (tender, curious synthetic male voice), an artificial companion, attends his human owners' 50th wedding anniversary. "
            "He asks the bride, Clara (warm, graceful elderly woman voice), what algorithm kept them together through poverty, illness, and old age. "
            "Clara takes Orion's metallic hand and explains: 'Marriage isn't an algorithm, Orion. It's choosing to forgive someone every morning, even when they burn the toast.'"
        )
    },
    {
        "id": 3,
        "topic": (
            "The Grumpy Baker and the Flower Girl. "
            "Marco (grumpy, deep-voiced Italian baker) pretends to be annoyed when Elena (bright, melodious, cheerful young florist) brings a fresh daisy to his bakery every sunrise. "
            "When Elena catches a severe fever and doesn't show up for three days, the fierce baker panics, runs across the cobblestone city with a hot basket of fresh almond croissants and honey tea, "
            "finally confessing his feelings at her doorstep."
        )
    },
    {
        "id": 4,
        "topic": (
            "The Forgotten Love Letter in the Attic. "
            "Leo (thoughtful young husband voice) finds a faded, handwritten letter tucked behind a floorboard in their new Victorian home from 1920. "
            "He reads it aloud to his wife Maya (touched, emotional female voice)—a soldier's vow to return home to his bride. "
            "The final sentence reveals a golden ring buried in the brickwork, inspiring Leo to reaffirm his own eternal vows to Maya under the candlelit attic."
        )
    },
    {
        "id": 5,
        "topic": (
            "The Billionaire's Secret Vow. "
            "Julian (deep, protective, wealthy CEO male voice) gives up his entire corporate empire when his board of directors tries to force him to sign an annulment from his humble, sweet-hearted wife Sarah (soft, resilient, loving woman voice). "
            "Julian walks into the boardroom, tosses his gold credentials onto the mahogany table, and says: 'Keep the billions. I built this company with my hands, but she built my soul.'"
        )
    },
    {
        "id": 6,
        "topic": (
            "The Memory Jar. "
            "Thomas (patient, devoted elderly husband voice) visits his wife Rose (fragile, gentle woman voice) every single afternoon in a sunlit garden, introducing himself as if they are meeting for the first time. "
            "He brings her favorite blueberry tart and retells the story of how they fell in love at 19. "
            "When Rose suddenly looks into his eyes, smiles, and whispers, 'I may forget my name, Tommy, but my heart never forgot yours,' Thomas's eyes fill with tears of joy."
        )
    },
    {
        "id": 7,
        "topic": (
            "The Lighthouse Keeper's Golden Beacon. "
            "Captain Douglas (weathered, hearty sea captain voice) is caught in the most violent winter gale off the rocky cliffs. "
            "His ship's compass shatters, but through the pitch-black hurricane, a radiant golden light cuts through the fog. "
            "His bride Abigail (brave, melodic woman voice) has kept the ancient lighthouse oil fire burning for 48 hours without sleep, guiding him safely back into her arms."
        )
    },
    {
        "id": 8,
        "topic": (
            "The First Dance Under the Midnight Rain. "
            "On their wedding day, a sudden torrential summer storm collapses the luxury reception tent. "
            "While the guests gasp, the groom Noah (playful, deeply in love young male voice) laughs, takes his bride Sophie's (radiant, breathless female voice) hand, and pulls her into the open grass. "
            "Soaked in rain, they dance their first dance under the starry thunderstorm, creating a moment more magical than any ballroom could hold."
        )
    },
    {
        "id": 9,
        "topic": (
            "The King Who Chose the Village Seamstress. "
            "King Valen (regal, commanding yet deeply gentle king's voice) is commanded by the Royal Council to marry a foreign princess for political power. "
            "Instead, before the entire assembled kingdom, Valen steps down from his throne, kneels before Linnea, a kind village seamstress (humble, pure-hearted young woman voice) who saved his life in the forest, "
            "and crowns her his Queen, declaring: 'A crown is worthless if I cannot share it with the one who owns my heart.'"
        )
    },
    {
        "id": 10,
        "topic": (
            "The Secret Sticky Notes of 40 Years. "
            "Grace (nostalgic, smiling woman voice) discovers a wooden keepsake box in her late husband Daniel's (affectionate, teasing male voice) study. "
            "Inside are over 10,000 tiny yellow sticky notes he secretly hid in her lunchbox, car, and coat pockets every single workday for 40 years, each reading a simple reason why he loved her that day. "
            "The final note on top reads: 'In every lifetime, I will look for you first.'"
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

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
            "The Father Who Never Stopped Watching (The Prodigal Son). "
            "Eliab, an elderly father with tear-stained eyes (warm, weeping elder voice), watches the dusty road every evening praying for his lost son Caleb (broken, trembling young man voice). "
            "When Caleb crawls back in filthy rags expecting rejection, the father runs, throws his arms around his neck, and restores him with a royal robe, crying: 'My son was dead, and is alive again! To God be all the glory!'"
        )
    },
    {
        "id": 2,
        "topic": (
            "The Roman Centurion's Great Faith. "
            "Marcus, a battle-hardened Roman centurion in shining bronze armor (commanding, humble male voice), kneels in the dust before the Lord for his paralyzed dying servant. "
            "He says: 'Lord, I am not worthy for you to come under my roof; speak the word only, and my servant shall be healed.' "
            "Heaven rejoices as the servant rises completely healed at that very hour, glorifying the Almighty God!"
        )
    },
    {
        "id": 3,
        "topic": (
            "The Fourth Man in the Fiery Furnace. "
            "Azariah (courageous, steadfast young Hebrew voice) and his brothers refuse to bow to King Nebuchadnezzar's golden idol, declaring their God is able to save them. "
            "Thrown bound into a furnace heated seven times hotter, their ropes burn away, and an astonished king gasps seeing four men walking freely in the fire, untouched by flames, with the fourth shining like the Son of God!"
        )
    },
    {
        "id": 4,
        "topic": (
            "The Blind Beggar at Jericho (Bartimaeus). "
            "Bartimaeus, a ragged blind beggar sitting outside Jericho (crying out with desperate, passionate voice), hears Jesus of Nazareth passing. "
            "Though the harsh crowd scolds him to be silent, he shouts louder: 'Jesus, Son of David, have mercy on me!' "
            "The Savior stops, asks what he desires, and says: 'Go your way; your faith has made you whole!' His eyes open to see light and his Savior, leaping and glorifying God!"
        )
    },
    {
        "id": 5,
        "topic": (
            "The Widow's Unfailing Jar of Oil. "
            "Sarah, a starving widow in Zarephath (gentle, exhausted mother voice), gathers two sticks to prepare her very last meal of flour and oil for her dying son. "
            "The prophet Elijah (reverent, faithful prophet voice) tells her: 'Fear not, for thus says the Lord God of Israel: the jar of flour shall not be spent, neither shall the jug of oil fail.' "
            "In faith she bakes the bread, and God miraculously multiplies the jars for months!"
        )
    },
    {
        "id": 6,
        "topic": (
            "Peace, Be Still: The Calming of the Storm. "
            "Peter, a terrified fisherman (frantic, breathless voice), battles mountain-high waves and a sinking boat in the pitch-black Sea of Galilee, crying: 'Lord, do You not care that we perish?' "
            "Jesus rises in majestic peace, raises His hand against the roaring storm, and commands: 'Peace, be still!' "
            "The howling gale instantly dies into glass-like calm, leaving the disciples whispering in awe: 'Who is this, that even the wind and the sea obey Him?'"
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

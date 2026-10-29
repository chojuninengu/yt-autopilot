import os
import argparse
import sys
import time
import json
import datetime
from pathlib import Path

from .config import STUDIO_DIR, PROJECT_ROOT, OUTPUT_DIR
from .story_engine import generate_story
from .image_engine import generate_scene_images
from .video_fetcher import get_scene_video_clip
from .audio_engine import generate_voiceover
from .video_engine import assemble_cinematic_video, assemble_moving_clips_video
from .battle_engine import generate_battle_story
from .multi_voice import render_battle_audio
from .battle_visuals import render_battle_video
from .fable_engine import generate_fable_story
from .fable_audio import render_fable_audio
from .fable_visuals import render_fable_video
from .publisher import publish_video

def run_fable_video(
    index: int,
    total: int,
    topic: str = "The Banana farmer and the greedy Watermelon neighbor",
    publish: bool = True,
    platforms: list = None
):
    print("\n" + "="*60)
    print(f"🍌 LOCAL STUDIO: Generating 3D Character Fable {index}/{total}")
    print(f"📖 Story Topic: {topic}")
    print("="*60)
    start_time = time.time()

    timestamp = int(time.time())
    run_dir = OUTPUT_DIR / f"fable_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    # 1. Fable Script Planning
    print("\n[Step 1/4] 🧠 Scripting viral 3D character fable with Gemini...")
    fable_plan = generate_fable_story(topic)
    (run_dir / "fable_plan.json").write_text(json.dumps(fable_plan, indent=2))

    # 2. Emotional Voice Acting + SFX
    print("\n[Step 2/4] 🎙️ Directing emotional voice acting and mixing story SFX...")
    scene_meta, master_audio, srt_path = render_fable_audio(fable_plan, run_dir)

    # 3. 3D Pixar Visual Frames (Generated with Agnes AI 3D engine / SD-Turbo fallback)
    print("\n[Step 3/4] 🎨 Rendering 3D Pixar character scene frames...")
    scenes = fable_plan.get("scenes", [])
    mode = "agnes" if os.getenv("AGNES_API_KEY") else "local"
    image_paths = generate_scene_images(scenes, run_dir, mode=mode)

    # 4. Cinematic Fable Assembly (Emotional zooms, impact shakes, centered subtitles)
    print("\n[Step 4/4] 🎞️ Assembling 3D animated fable with centered viral captions...")
    final_video = run_dir / f"fable_video_{timestamp}.mp4"
    success = render_fable_video(
        image_paths=image_paths,
        scene_meta=scene_meta,
        master_audio=master_audio,
        srt_path=srt_path,
        output_path=final_video
    )

    if not success or not final_video.exists():
        print("❌ Fable video assembly failed.")
        return False

    elapsed = time.time() - start_time
    print(f"✅ 3D Character Fable created in {elapsed:.1f}s ({elapsed/60:.1f} mins)!")
    print(f"📁 Video Location: {final_video}")

    # 5. Publishing
    if publish:
        print(f"\n[Step 5/5] 🚀 Publishing fable to {platforms}...")
        results = publish_video(final_video, fable_plan, platforms=platforms)
        print(f"🏁 Published Results: {results}")
    else:
        print("\n[Step 5/5] ⏭️ Skipping publishing (--no-publish active).")

    return True

def run_battle_video(
    index: int,
    total: int,
    topic: str = "Superman against Metro Man",
    publish: bool = True,
    platforms: list = None
):
    print("\n" + "="*60)
    print(f"🥊 LOCAL STUDIO: Generating Character Battle {index}/{total}")
    print(f"⚔️ Topic: {topic}")
    print("="*60)
    start_time = time.time()

    timestamp = int(time.time())
    run_dir = OUTPUT_DIR / f"battle_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    # 1. Battle Script Planning
    print("\n[Step 1/4] 🧠 Directing multi-character battle script with Gemini...")
    battle_plan = generate_battle_story(topic)
    (run_dir / "battle_plan.json").write_text(json.dumps(battle_plan, indent=2))

    # 2. Multi-Character Voices + SFX
    print("\n[Step 2/4] 🎙️ Synthesizing multiple character voices and mixing battle SFX...")
    scene_meta, master_audio, srt_path = render_battle_audio(battle_plan, run_dir)

    # 3. Action Visuals
    print("\n[Step 3/4] 🎨 Rendering character action frames...")
    scenes = battle_plan.get("scenes", [])
    image_paths = generate_scene_images(scenes, run_dir, mode="auto")

    # 4. VFX Assembly (Screen shake, white flash, subtitles)
    print("\n[Step 4/4] 💥 Assembling battle video with camera screen-shakes and impact flashes...")
    final_video = run_dir / f"battle_video_{timestamp}.mp4"
    success = render_battle_video(
        image_paths=image_paths,
        scene_meta=scene_meta,
        master_audio=master_audio,
        srt_path=srt_path,
        output_path=final_video
    )

    if not success or not final_video.exists():
        print("❌ Battle video assembly failed.")
        return False

    elapsed = time.time() - start_time
    print(f"✅ Battle video created in {elapsed:.1f}s ({elapsed/60:.1f} mins)!")
    print(f"📁 Video Location: {final_video}")

    # 5. Publishing
    if publish:
        print(f"\n[Step 5/5] 🚀 Publishing battle to {platforms}...")
        results = publish_video(final_video, battle_plan, platforms=platforms)
        print(f"🏁 Published Results: {results}")
    else:
        print("\n[Step 5/5] ⏭️ Skipping publishing (--no-publish active).")

    return True

def run_single_video(
    index: int,
    total: int,
    topic: str = None,
    mode: str = "local",
    visual_type: str = "moving",
    duration_target: int = 60,
    publish: bool = True,
    platforms: list = None
):
    print("\n" + "="*60)
    print(f"🎬 LOCAL STUDIO: Generating Video {index}/{total} (Target: {duration_target}s, Type: {visual_type})")
    print("="*60)
    start_time = time.time()

    timestamp = int(time.time())
    run_dir = OUTPUT_DIR / f"run_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    # 1. Story & Scene Planning
    print(f"\n[Step 1/5] 🧠 Generating viral story with Gemini ({duration_target}s)...")
    story = generate_story(topic, duration_seconds=duration_target)
    title = story.get("title", f"Documentary #{index}")
    plan_file = run_dir / "plan.json"
    plan_file.write_text(json.dumps(story, indent=2))

    # 2. Voiceover & Subtitles
    print("\n[Step 2/5] 🎙️ Synthesizing documentary narration with Edge-TTS...")
    narration = story.get("narration", "")
    audio_path, srt_path, duration = generate_voiceover(narration, run_dir)

    scenes = story.get("scenes", [])
    num_scenes = len(scenes)
    scene_dur = duration / max(num_scenes, 1)

    final_video = run_dir / f"final_video_{timestamp}.mp4"

    # 3. Visuals Generation & Assembly
    if visual_type == "moving":
        print(f"\n[Step 3/5] 🎥 Sourcing {num_scenes} real moving animated video clips...")
        clip_paths = []
        for i, sc in enumerate(scenes):
            idx = sc.get("scene_number", i + 1)
            clip_file = run_dir / f"clip_{idx:02d}.mp4"
            print(f"[VideoFetcher] Sourcing Scene {idx}/{num_scenes}...")
            ok = get_scene_video_clip(sc, clip_file, duration=scene_dur)
            if ok and clip_file.exists():
                clip_paths.append(clip_file)
            else:
                print(f"[VideoFetcher] Video fetch fallback for Scene {idx}, generating visual image...")
                img_file = run_dir / f"scene_{idx:02d}.jpg"
                generate_scene_images([sc], run_dir, mode=mode)
                clip_paths.append(img_file)

        print(f"\n[Step 4/5] 🎞️ Assembling {len(clip_paths)} moving clips into final video...")
        success = assemble_moving_clips_video(
            clip_paths=clip_paths,
            audio_path=audio_path,
            srt_path=srt_path,
            output_path=final_video
        )
    else:
        print(f"\n[Step 3/5] 🎨 Rendering {num_scenes} scene images (Mode: {mode})...")
        image_paths = generate_scene_images(scenes, run_dir, mode=mode)
        print("\n[Step 4/5] 🎞️ Assembling dynamic cinematic vertical video (1080x1920)...")
        success = assemble_cinematic_video(
            image_paths=image_paths,
            audio_path=audio_path,
            srt_path=srt_path,
            total_duration=duration,
            output_path=final_video
        )

    if not success or not final_video.exists():
        print("❌ Video assembly failed.")
        return False

    elapsed = time.time() - start_time
    print(f"✅ Video created in {elapsed:.1f}s ({elapsed/60:.1f} mins)!")
    print(f"📁 Video Location: {final_video}")

    # 5. Publishing
    if publish:
        print(f"\n[Step 5/5] 🚀 Publishing to {platforms}...")
        results = publish_video(final_video, story, platforms=platforms)
        print(f"🏁 Published Results: {results}")
    else:
        print("\n[Step 5/5] ⏭️ Skipping publishing (--no-publish active).")

    return True

def main():
    parser = argparse.ArgumentParser(description="Local Studio: Fast, 100% Free AI Video Creation and Publishing")
    parser.add_argument("--count", type=int, default=1, help="Number of videos to generate in batch (default: 1)")
    parser.add_argument("--topic", type=str, default=None, help="Custom topic or prompt (optional)")
    parser.add_argument("--duration", type=int, default=60, help="Target duration in seconds (e.g. 60 or 120 for 2 mins)")
    parser.add_argument("--type", choices=["moving", "static"], default="moving", help="Visual type: 'moving' (real animated moving video clips), 'static' (still images with motion)")
    parser.add_argument("--mode", choices=["local", "fast", "auto"], default="local", help="Image generator mode for fallback")
    parser.add_argument("--fable", action="store_true", help="Generate viral 3D animated character fable (matching @heystoriefunny style)")
    parser.add_argument("--battle", action="store_true", help="Generate multi-character battle showdown with distinct voices, sound effects, and ground-shaking impacts")
    parser.add_argument("--no-publish", action="store_true", help="Generate video only without uploading")
    parser.add_argument("--platforms", type=str, default="youtube,tiktok", help="Comma-separated platforms: youtube,tiktok")

    args = parser.parse_args()
    selected_platforms = [p.strip().lower() for p in args.platforms.split(",") if p.strip()]

    print("\n" + "#"*60)
    if args.fable:
        mode_label = "3D Character Fable & Moral Story (@heystoriefunny style)"
    elif args.battle:
        mode_label = "Character Battle & Showdown"
    else:
        mode_label = f"Standard ({args.type})"

    print(f"🚀 LOCAL AI VIDEO STUDIO (Mode: {mode_label})")
    print(f"• Batch Count: {args.count}")
    if not (args.fable or args.battle):
        print(f"• Target Duration: {args.duration}s")
        print(f"• Visual Type: {args.type}")
    print(f"• Platforms: {selected_platforms if not args.no_publish else 'None (dry-run)'}")
    print("#"*60)

    success_count = 0
    total_start = time.time()

    for i in range(1, args.count + 1):
        try:
            if args.fable:
                topic = args.topic or "The Banana farmer and the greedy Watermelon neighbor"
                ok = run_fable_video(
                    index=i,
                    total=args.count,
                    topic=topic,
                    publish=not args.no_publish,
                    platforms=selected_platforms
                )
            elif args.battle:
                topic = args.topic or "Superman against Metro Man"
                ok = run_battle_video(
                    index=i,
                    total=args.count,
                    topic=topic,
                    publish=not args.no_publish,
                    platforms=selected_platforms
                )
            else:
                ok = run_single_video(
                    index=i,
                    total=args.count,
                    topic=args.topic,
                    mode=args.mode,
                    visual_type=args.type,
                    duration_target=args.duration,
                    publish=not args.no_publish,
                    platforms=selected_platforms
                )
            if ok:
                success_count += 1
        except KeyboardInterrupt:
            print("\nStopped by user.")
            break
        except Exception as e:
            print(f"⚠️ Error in video {i}: {e}")

    total_time = time.time() - total_start
    print("\n" + "="*60)
    print(f"🎉 BATCH COMPLETE: {success_count}/{args.count} videos generated in {total_time:.1f}s ({total_time/60:.1f}m)")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()

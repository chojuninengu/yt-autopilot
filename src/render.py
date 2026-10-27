"""Phase 2 - Render video pipeline: voiceover + stock footage/fallback + styled subtitles."""
import os
import pathlib
import re
import shutil
import subprocess
import tempfile

from footage import fetch_stock_clip, prepare_scene_clip
from imagegen import generate_image
from voice import DEFAULT_VOICE, generate_voiceover


def build_motion_filter(motion: str, duration_sec: float, fps: int = 30) -> str:
    """Build FFmpeg zoompan filter string for animated still with jitter prevention."""
    d = max(1, int(round(duration_sec * fps)))
    # Scale up input 2x first before zoompan to eliminate micro-jitter
    scale_prefix = "scale=2160:3840:force_original_aspect_ratio=increase,crop=2160:3840"

    if motion == "zoom_in":
        zoompan_expr = (
            f"zoompan=z='1.0+0.15*(on/{d})':"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={d}:s=1080x1920:fps={fps}"
        )
    elif motion == "zoom_out":
        zoompan_expr = (
            f"zoompan=z='1.15-0.15*(on/{d})':"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={d}:s=1080x1920:fps={fps}"
        )
    elif motion == "pan_left":
        zoompan_expr = (
            f"zoompan=z='1.12':"
            f"x='(iw-iw/zoom)*(1.0-(on/{d}))':y='ih/2-(ih/zoom/2)':d={d}:s=1080x1920:fps={fps}"
        )
    elif motion == "pan_right":
        zoompan_expr = (
            f"zoompan=z='1.12':"
            f"x='(iw-iw/zoom)*(on/{d})':y='ih/2-(ih/zoom/2)':d={d}:s=1080x1920:fps={fps}"
        )
    elif motion == "shake":
        zoompan_expr = (
            f"zoompan=z='1.08':"
            f"x='iw/2-(iw/zoom/2)+15*sin(2*PI*on/15)+10*cos(2*PI*on/23)':"
            f"y='ih/2-(ih/zoom/2)+15*cos(2*PI*on/17)+10*sin(2*PI*on/29)':d={d}:s=1080x1920:fps={fps}"
        )
    else:  # fallback to zoom_in
        zoompan_expr = (
            f"zoompan=z='1.0+0.15*(on/{d})':"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={d}:s=1080x1920:fps={fps}"
        )

    return f"{scale_prefix},{zoompan_expr}"


def prepare_still_clip(img_path: pathlib.Path, output_clip: pathlib.Path, duration: float, motion: str = "zoom_in"):
    """Convert a still image into an animated 1080x1920 30fps clip using subtle zoompan motion."""
    vf = build_motion_filter(motion, duration, fps=30)
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(img_path),
        "-vf", vf,
        "-t", f"{duration:.2f}",
        "-c:v", "libx264",
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        str(output_clip)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def create_placeholder_still(out_path: pathlib.Path, label: str = "", index: int = 0):
    """Generate a quick local colored 768x1344 placeholder image using FFmpeg."""
    colors = ["#1e1b4b", "#0f172a", "#064e3b", "#3b0764", "#1c1917", "#172554"]
    color = colors[index % len(colors)]
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c={color}:s=768x1344:d=1",
        "-frames:v", "1",
        str(out_path)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def get_audio_duration(audio_path: pathlib.Path) -> float:
    """Measure exact audio duration in seconds using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(audio_path)
    ]
    out = subprocess.check_output(cmd, text=True).strip()
    return float(out)


def wrap_srt_lines(srt_content: str, max_chars: int = 30) -> str:
    """Wrap subtitle lines to fit neatly on vertical 9:16 mobile screens."""
    blocks = re.split(r"\n\s*\n", srt_content.strip())
    wrapped_blocks = []

    for block in blocks:
        lines = block.split("\n")
        if len(lines) < 3:
            wrapped_blocks.append(block)
            continue

        index_line = lines[0]
        time_line = lines[1]
        text_lines = lines[2:]
        full_text = " ".join(text_lines)

        words = full_text.split()
        wrapped_text = []
        curr = []
        curr_len = 0
        for w in words:
            if curr_len + len(w) + 1 > max_chars and curr:
                wrapped_text.append(" ".join(curr))
                curr = [w]
                curr_len = len(w)
            else:
                curr.append(w)
                curr_len += len(w) + 1
        if curr:
            wrapped_text.append(" ".join(curr))

        wrapped_blocks.append(f"{index_line}\n{time_line}\n" + "\n".join(wrapped_text))

    return "\n\n".join(wrapped_blocks) + "\n"


def render_video(plan: dict, output_file: pathlib.Path, cfg: dict | None = None) -> pathlib.Path:
    """Render a complete vertical video with voiceover, footage, and burned-in captions."""
    cfg = cfg or {}
    voice = cfg.get("voice", DEFAULT_VOICE)
    visual_mode = cfg.get("visual_mode", "cartoon_stills")
    dry_run = cfg.get("dry_run", False) or os.environ.get("DRY_RUN", "0") in ("1", "true")

    output_file.parent.mkdir(parents=True, exist_ok=True)

    script = plan.get("script", "").strip()
    if not script:
        raise ValueError("Plan contains no script to render.")

    scenes = plan.get("scenes", [])
    if not scenes:
        scenes = [{"narration": script, "visual_keywords": ["trending", "viral"]}]

    work_dir = pathlib.Path(tempfile.mkdtemp(prefix="render_"))
    try:
        audio_file = work_dir / "voice.mp3"
        srt_file = work_dir / "subtitles.srt"

        print(f"Generating voiceover with {voice}...")
        generate_voiceover(script, audio_file, srt_file, voice=voice)

        # Re-wrap subtitles for vertical format
        raw_srt = srt_file.read_text(encoding="utf-8")
        srt_file.write_text(wrap_srt_lines(raw_srt), encoding="utf-8")

        total_duration = get_audio_duration(audio_file)
        print(f"Voiceover duration: {total_duration:.2f}s across {len(scenes)} scenes")

        # Duration per scene
        scene_duration = total_duration / len(scenes)

        scene_clip_paths = []
        cache_dir = work_dir / "footage_cache"

        for idx, scene in enumerate(scenes):
            keywords = scene.get("visual_keywords", ["technology"])
            motion = scene.get("motion", "zoom_in")
            scene_clip = work_dir / f"scene_{idx:03d}.mp4"

            if visual_mode == "cartoon_stills":
                try:
                    img_path = work_dir / f"scene_img_{idx:03d}.png"
                    if dry_run:
                        create_placeholder_still(img_path, scene.get("image_prompt", scene["narration"]), idx)
                        provider_used = "mock_placeholder"
                    else:
                        prompt = scene.get("image_prompt") or scene["narration"]
                        print(f"Generating cartoon image for scene {idx + 1}/{len(scenes)} (motion: {motion})...")
                        provider_used = generate_image(prompt, img_path, cfg=cfg, seed=42 + idx)

                    prepare_still_clip(img_path, scene_clip, scene_duration, motion=motion)
                    scene["provider"] = provider_used
                    print(f"Scene {idx + 1} rendered using '{provider_used}' with {motion} motion.")
                except Exception as ex:
                    print(f"Cartoon image generation failed for scene {idx + 1} ({ex}); falling back to stock clip...")
                    raw_clip = fetch_stock_clip(keywords, cache_dir)
                    prepare_scene_clip(raw_clip, scene_clip, scene_duration, scene_index=idx)
                    scene["provider"] = "stock"
            else:
                # Stock footage visual mode
                print(f"Preparing scene {idx + 1}/{len(scenes)} from stock footage (keywords: {keywords})...")
                raw_clip = fetch_stock_clip(keywords, cache_dir)
                prepare_scene_clip(raw_clip, scene_clip, scene_duration, scene_index=idx)
                scene["provider"] = "stock"

            scene_clip_paths.append(scene_clip)

        # Concatenate scene clips
        concat_list_file = work_dir / "concat_list.txt"
        with open(concat_list_file, "w", encoding="utf-8") as f:
            for p in scene_clip_paths:
                f.write(f"file '{p.resolve()}'\n")

        stitched_video = work_dir / "stitched.mp4"
        subprocess.run([
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list_file),
            "-c", "copy",
            str(stitched_video)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Final compose: merge stitched video + audio + burn subtitles
        print("Muxing audio and burning stylized subtitles...")
        srt_escaped = str(srt_file.resolve()).replace("\\", "/").replace(":", "\\:")
        sub_filter = (
            f"subtitles='{srt_escaped}':force_style="
            f"'PlayResX=1080,PlayResY=1920,Fontname=DejaVu Sans,Fontsize=52,Bold=1,"
            f"PrimaryColour=&H0000FFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=3,"
            f"Shadow=2,Alignment=2,MarginV=320'"
        )

        final_temp = work_dir / "final.mp4"
        subprocess.run([
            "ffmpeg", "-y",
            "-i", str(stitched_video),
            "-i", str(audio_file),
            "-vf", sub_filter,
            "-c:v", "libx264",
            "-preset", "fast",
            "-c:a", "aac",
            "-b:a", "192k",
            "-t", f"{total_duration:.2f}",
            "-pix_fmt", "yuv420p",
            str(final_temp)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        shutil.copy2(final_temp, output_file)
        print(f"Video rendered successfully: {output_file}")
        return output_file
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)

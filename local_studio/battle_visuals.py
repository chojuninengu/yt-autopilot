import subprocess
from pathlib import Path
from typing import List, Dict, Any

def render_battle_video(
    image_paths: List[Path],
    scene_meta: List[Dict[str, Any]],
    master_audio: Path,
    srt_path: Path,
    output_path: Path,
    width: int = 1080,
    height: int = 1920,
    fps: int = 30
) -> bool:
    """Assembles character showdown video with violent impact screen-shakes, impact flashes, and color-coded subtitles."""
    work_dir = output_path.parent
    temp_clips = []

    print(f"[BattleVisuals] Rendering {len(scene_meta)} action-packed battle clips with VFX...")

    for idx, (img, meta) in enumerate(zip(image_paths, scene_meta)):
        clip_path = work_dir / f"battle_clip_{idx:02d}.mp4"
        temp_clips.append(clip_path)

        duration = meta.get("duration", 4.0)
        num_frames = int(duration * fps)
        is_shake = meta.get("shake", False)

        if is_shake:
            # High-impact screen shake with white flash on impact
            vf = (
                f"scale={width+80}:{height+80},"
                f"crop=w={width}:h={height}:x='(iw-ow)/2 + 25*sin(50*t)*exp(-3.5*t)':y='(ih-oh)/2 + 20*cos(45*t)*exp(-3.5*t)',"
                f"fade=in:st=0:d=0.08:color=white"
            )
        elif idx % 2 == 0:
            # Smooth aggressive zoom-in
            vf = (
                f"scale={width*2}:{height*2},"
                f"zoompan=z='min(zoom+0.0025,1.35)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                f"d={num_frames}:s={width}x{height}:fps={fps}"
            )
        else:
            # Supersonic zoom-out / pan drift
            vf = (
                f"scale={width*2}:{height*2},"
                f"zoompan=z='if(lte(zoom,1.0),1.3,max(1.001,zoom-0.002))':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                f"d={num_frames}:s={width}x{height}:fps={fps}"
            )

        cmd = [
            "ffmpeg", "-y", "-loop", "1", "-i", str(img),
            "-vf", vf,
            "-t", str(duration),
            "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
            str(clip_path)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    concat_txt = work_dir / "battle_clips.txt"
    with open(concat_txt, "w") as f:
        for c in temp_clips:
            if c.exists() and c.stat().st_size > 1000:
                f.write(f"file '{c.resolve()}'\n")

    unsubbed = work_dir / "unsubbed_battle.mp4"
    concat_cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_txt),
        "-i", str(master_audio),
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        "-shortest", str(unsubbed)
    ]
    subprocess.run(concat_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Burn dynamic action captions
    if srt_path.exists() and srt_path.stat().st_size > 10:
        print("[BattleVisuals] Burning battle captions with character names into video...")
        escaped_srt = str(srt_path.resolve()).replace(":", "\\:").replace("'", "\\'")
        sub_filter = (
            f"subtitles='{escaped_srt}':force_style="
            f"'FontName=Arial Black,FontSize=20,PrimaryColour=&H0000FFFF,OutlineColour=&H00000000,BorderStyle=3,Outline=3,Alignment=2,MarginV=200'"
        )
        final_cmd = [
            "ffmpeg", "-y", "-i", str(unsubbed),
            "-vf", sub_filter,
            "-c:v", "libx264", "-preset", "fast", "-c:a", "copy",
            str(output_path)
        ]
        subprocess.run(final_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if not output_path.exists():
            unsubbed.rename(output_path)
    else:
        unsubbed.rename(output_path)

    # Clean intermediate clips
    for c in temp_clips:
        if c.exists():
            c.unlink()
    if concat_txt.exists():
        concat_txt.unlink()
    if unsubbed.exists():
        unsubbed.unlink()

    if output_path.exists() and output_path.stat().st_size > 10000:
        print(f"[BattleVisuals] Battle Video Ready: {output_path} ({output_path.stat().st_size / 1024 / 1024:.2f} MB)")
        return True
    return False

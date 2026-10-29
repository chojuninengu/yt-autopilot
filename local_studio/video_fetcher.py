import os
import time
import subprocess
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional

def query_huggingface_video(prompt: str, output_path: Path, hf_token: Optional[str] = None) -> bool:
    """Attempts to generate a real AI moving video clip via Hugging Face Gradio client."""
    token = hf_token or os.getenv("HF_TOKEN")
    try:
        headers = {"Authorization": f"Bearer {token}"} if token else None
        client = Client("Lightricks/ltx-video-distilled", headers=headers)
        result = client.predict(
            prompt=f"{prompt}, cinematic, photorealistic, 8k, fluid motion",
            negative_prompt="worst quality, blurry, jittery, distorted",
            input_image_filepath=None,
            input_video_filepath=None,
            height_ui=512,
            width_ui=704,
            mode="text-to-video",
            duration_ui=2,
            ui_frames_to_use=9,
            seed_ui=42,
            randomize_seed=True,
            ui_guidance_scale=1,
            improve_texture_flag=True,
            api_name="/text_to_video"
        )
        if result and isinstance(result, (tuple, list)) and len(result) > 0:
            video_info = result[0]
            clip_path = video_info.get("video") if isinstance(video_info, dict) else str(video_info)
            if clip_path and Path(clip_path).exists():
                import shutil
                shutil.copy(clip_path, output_path)
                print(f"[VideoFetcher] Hugging Face AI video generated: {output_path.name}")
                return True
    except Exception as e:
        print(f"[VideoFetcher] Hugging Face video generation notice: {e}")
    return False

def fetch_pixabay_moving_video(query: str, output_path: Path, duration_target: float = 8.0, width: int = 1080, height: int = 1920) -> bool:
    """Fetches a real moving HD video clip from Pixabay (100% free, royalty-free, moving 4k/HD footage)."""
    api_key = os.getenv("PIXABAY_API_KEY", "")
    if not api_key:
        return False

    # Extract keywords
    words = [
        w for w in query.replace(",", " ").split()
        if len(w) > 3 and w.lower() not in {"shot", "scene", "photorealistic", "ultra", "detailed", "cinematic", "focus", "atmosphere", "style", "view"}
    ]
    search_query = "+".join(words[:4]) or "nature"

    url = f"https://pixabay.com/api/videos/?key={api_key}&q={search_query}&per_page=6"
    try:
        res = requests.get(url, timeout=15)
        if res.status_code == 200:
            hits = res.json().get("hits", [])
            if hits:
                # Pick the best matching hit
                video_url = hits[0].get("videos", {}).get("medium", {}).get("url") or hits[0].get("videos", {}).get("small", {}).get("url")
                if video_url:
                    raw_clip = output_path.parent / f"raw_{output_path.name}"
                    resp = requests.get(video_url, timeout=30)
                    with open(raw_clip, "wb") as f:
                        f.write(resp.content)

                    # Crop and scale into vertical 1080x1920 30fps MP4
                    scale_filter = (
                        f"scale={width}:{height}:force_original_aspect_ratio=increase,"
                        f"crop={width}:{height}"
                    )
                    ffmpeg_cmd = [
                        "ffmpeg", "-y", "-i", str(raw_clip),
                        "-t", str(duration_target),
                        "-vf", scale_filter,
                        "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
                        "-an", str(output_path)
                    ]
                    subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    if raw_clip.exists():
                        raw_clip.unlink()

                    if output_path.exists() and output_path.stat().st_size > 10000:
                        print(f"[VideoFetcher] Real moving video clip saved: {output_path.name}")
                        return True
    except Exception as e:
        print(f"[VideoFetcher] Pixabay video fetch error: {e}")

    return False

def get_scene_video_clip(scene: Dict[str, Any], output_path: Path, duration: float) -> bool:
    """Attempts to get a real moving video clip for the scene.
    Order:
      1. Hugging Face AI text-to-video (Wan2.1 / LTX-Video)
      2. Pixabay HD moving footage
    """
    prompt = scene.get("image_prompt") or scene.get("narration_fragment", "")
    
    # 1. Try Hugging Face
    success = query_huggingface_video(prompt, output_path)
    if success:
        return True

    # 2. Try Pixabay real moving video
    success = fetch_pixabay_moving_video(prompt, output_path, duration_target=duration)
    return success

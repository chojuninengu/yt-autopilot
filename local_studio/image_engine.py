import os
import time
import urllib.parse
import requests
from pathlib import Path
from typing import List, Dict, Any
from PIL import Image

def generate_image_fast(prompt: str, output_path: Path, width: int = 1080, height: int = 1920) -> bool:
    """Generates a high-quality 9:16 vertical image using zero-token fast cloud endpoint (Pollinations).
    Cost: $0. Tokens: 0. Fast and hyper-realistic with smart 9:16 vertical cropping."""
    from io import BytesIO

    clean_prompt = f"{prompt}, photorealistic 8k, national geographic, cinematic lighting, 35mm photograph, masterwork"
    encoded_prompt = urllib.parse.quote(clean_prompt)
    seed = int(time.time() * 1000) % 1000000

    # Try endpoints in sequence
    urls_to_try = [
        f"https://image.pollinations.ai/prompt/{encoded_prompt}?nologo=true&seed={seed}",
        f"https://image.pollinations.ai/prompt/{encoded_prompt}?model=flux&nologo=true&seed={seed}",
    ]

    for url in urls_to_try:
        try:
            res = requests.get(url, timeout=35)
            if res.status_code == 200 and len(res.content) > 5000:
                raw_img = Image.open(BytesIO(res.content))
                # Smart crop & scale to exactly 1080x1920 vertical format
                scale = max(width / raw_img.width, height / raw_img.height)
                new_w = int(raw_img.width * scale)
                new_h = int(raw_img.height * scale)
                resized = raw_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                
                left = (new_w - width) // 2
                top = (new_h - height) // 2
                final_img = resized.crop((left, top, left + width, top + height))
                final_img.save(output_path, quality=95)
                print(f"[ImageEngine] Fast image saved to {output_path.name}")
                return True
        except Exception as e:
            print(f"[ImageEngine] Warning: endpoint attempt failed ({e}), trying next...")
            continue

    print(f"[ImageEngine] All fast endpoints failed for prompt: '{prompt[:40]}...'")
    return False

_LOCAL_PIPELINE = None

def get_local_pipeline():
    """Lazily loads local Diffusers pipeline with SD-Turbo for instant 1-step CPU inference."""
    global _LOCAL_PIPELINE
    if _LOCAL_PIPELINE is not None:
        return _LOCAL_PIPELINE

    print("[ImageEngine] Loading local SD-Turbo model (1-step ultra fast)...")
    try:
        from diffusers import AutoPipelineForText2Image
        import torch

        _LOCAL_PIPELINE = AutoPipelineForText2Image.from_pretrained(
            "stabilityai/sd-turbo",
            torch_dtype=torch.float32
        )
        _LOCAL_PIPELINE.to("cpu")
        print("[ImageEngine] Local SD-Turbo model loaded successfully on CPU.")
        return _LOCAL_PIPELINE
    except Exception as e:
        print(f"[ImageEngine] Could not load local diffusers pipeline: {e}")
        return None

def generate_image_local(prompt: str, output_path: Path, width: int = 512, height: int = 512) -> bool:
    """Generates an image locally on your CPU/Arc GPU without internet or API keys using SD-Turbo."""
    pipe = get_local_pipeline()
    if pipe is None:
        return False

    try:
        # SD-Turbo runs with 1 single inference step and guidance_scale=0.0
        result = pipe(
            prompt=f"{prompt}, cinematic realism, 8k",
            num_inference_steps=1,
            guidance_scale=0.0,
            width=width,
            height=height
        )
        image = result.images[0]
        # Resize to vertical 1080x1920 using high-quality Lanczos upsampling
        image_vertical = image.resize((1080, 1920), Image.Resampling.LANCZOS)
        image_vertical.save(output_path, quality=95)
        print(f"[ImageEngine] Local image generated and saved to {output_path.name}")
        return True
    except Exception as e:
        print(f"[ImageEngine] Local generation failed: {e}")
        return False

def fetch_pixabay_stock(query: str, output_path: Path, width: int = 1080, height: int = 1920) -> bool:
    """Fallback: downloads a high-res royalty-free stock image from Pixabay."""
    from io import BytesIO
    api_key = os.getenv("PIXABAY_API_KEY", "")
    if not api_key:
        return False

    # Extract top keywords
    words = [w for w in query.replace(",", " ").split() if len(w) > 3 and w.lower() not in {"shot", "majestic", "cinematic", "photorealistic", "ultra", "detailed", "focus", "deep", "view", "scene"}]
    clean_q = "+".join(words[:4]) or "ocean"

    url = f"https://pixabay.com/api/?key={api_key}&q={clean_q}&image_type=photo&orientation=vertical&per_page=5"
    try:
        res = requests.get(url, timeout=15)
        if res.status_code == 200:
            hits = res.json().get("hits", [])
            if hits:
                img_url = hits[0].get("largeImageURL") or hits[0].get("webformatURL")
                img_res = requests.get(img_url, timeout=20)
                if img_res.status_code == 200:
                    raw_img = Image.open(BytesIO(img_res.content))
                    scale = max(width / raw_img.width, height / raw_img.height)
                    new_w = int(raw_img.width * scale)
                    new_h = int(raw_img.height * scale)
                    resized = raw_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    left = (new_w - width) // 2
                    top = (new_h - height) // 2
                    final_img = resized.crop((left, top, left + width, top + height))
                    final_img.save(output_path, quality=95)
                    print(f"[ImageEngine] Stock photo fallback saved to {output_path.name}")
                    return True
    except Exception as e:
        print(f"[ImageEngine] Pixabay stock fallback error: {e}")
    return False

def generate_image_agnes(prompt: str, output_path: Path, width: int = 1080, height: int = 1920) -> bool:
    """Generates ultra high-quality 3D character images using Agnes AI (agnes-image-2.5-flash)."""
    api_key = os.getenv("AGNES_API_KEY")
    if not api_key:
        return False
    try:
        payload = {
            "model": "agnes-image-2.5-flash",
            "prompt": f"{prompt}, 3D Disney Pixar character animation style, highly expressive, vibrant studio lighting, 8k render, octane render",
            "size": "720x1280"
        }
        res = requests.post(
            "https://apihub.agnes-ai.com/v1/images/generations",
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
            timeout=30
        )
        if res.status_code == 200:
            data = res.json().get("data", [])
            if data and data[0].get("url"):
                img_url = data[0]["url"]
                img_res = requests.get(img_url, timeout=30)
                if img_res.status_code == 200:
                    from io import BytesIO
                    raw_img = Image.open(BytesIO(img_res.content))
                    if raw_img.mode in ("RGBA", "P"):
                        raw_img = raw_img.convert("RGB")
                    resized = raw_img.resize((width, height), Image.Resampling.LANCZOS)
                    resized.save(output_path, "JPEG", quality=95)
                    print(f"[ImageEngine] Agnes AI 3D character image saved to {output_path.name}")
                    return True
    except Exception as e:
        print(f"[ImageEngine] Agnes image generation error: {e}")
    return False

def generate_scene_images(scenes: List[Dict[str, Any]], work_dir: Path, mode: str = "fast") -> List[Path]:
    """Generates images for each scene in the story plan with multi-layer fallback.
    Order:
      1. Agnes AI 3D Pixar Engine (if AGNES_API_KEY available)
      2. AI Fast Cloud (Pollinations)
      3. Local Offline SD-Turbo
      4. Pixabay Real Stock Photo (if rate-limited)
    """
    image_paths = []
    work_dir.mkdir(parents=True, exist_ok=True)

    for i, scene in enumerate(scenes):
        idx = scene.get("scene_number", i + 1)
        prompt = scene.get("image_prompt", "")
        out_file = work_dir / f"scene_{idx:02d}.jpg"

        print(f"[ImageEngine] Rendering Scene {idx}/{len(scenes)} (Mode: {mode})...")
        success = False

        if mode == "agnes" or os.getenv("AGNES_API_KEY"):
            success = generate_image_agnes(prompt, out_file)

        if not success:
            if mode == "local":
                success = generate_image_local(prompt, out_file)
                if not success:
                    print(f"[ImageEngine] Local generation not ready, using high-res stock photo for Scene {idx}...")
                    success = fetch_pixabay_stock(prompt, out_file)
            else:
                success = generate_image_fast(prompt, out_file)
                if not success:
                    print(f"[ImageEngine] Fast endpoint failed for Scene {idx}, checking Pixabay stock fallback...")
                    success = fetch_pixabay_stock(prompt, out_file)
                if not success and mode == "auto":
                    print("[ImageEngine] Falling back to local offline generation...")
                    success = generate_image_local(prompt, out_file)

        if success and out_file.exists():
            image_paths.append(out_file)
        else:
            # Re-use previous scene frame if available so it's NEVER a blank screen
            if image_paths and image_paths[-1].exists():
                print(f"[ImageEngine] Carrying forward previous frame for Scene {idx} to avoid blank screen.")
                prev_img = Image.open(image_paths[-1])
                prev_img.save(out_file)
                image_paths.append(out_file)
            else:
                # Atmospheric cinematic gradient instead of blank black
                from PIL import ImageDraw
                fallback_img = Image.new("RGB", (1080, 1920), color=(15, 23, 42))
                draw = ImageDraw.Draw(fallback_img)
                draw.rectangle([(0, 960), (1080, 1920)], fill=(30, 41, 59))
                fallback_img.save(out_file)
                image_paths.append(out_file)

        # Gentle pause between requests to respect rate limits
        time.sleep(1.2)

    return image_paths

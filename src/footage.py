"""Phase 2b - Fetch stock footage from free sources (Pixabay, Wikimedia, Pexels) or generate dynamic vertical background."""
import os
import pathlib
import subprocess
import requests

try:
    from dotenv import load_dotenv
    _env_path = pathlib.Path(__file__).resolve().parent.parent / ".env"
    if _env_path.exists():
        load_dotenv(dotenv_path=_env_path)
except ImportError:
    pass

PEXELS_SEARCH_URL = "https://api.pexels.com/videos/search"
PIXABAY_SEARCH_URL = "https://pixabay.com/api/videos/"
WIKIMEDIA_API_URL = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "yt-autopilot/0.2 (personal automated video creator)"}

PALETTES = [
    "0x0f172a",  # Slate 900
    "0x1e1b4b",  # Indigo 950
    "0x064e3b",  # Emerald 950
    "0x3b0764",  # Purple 950
    "0x1c1917",  # Stone 900
    "0x172554",  # Blue 950
]


def fetch_pixabay_clip(keywords: list[str], cache_dir: pathlib.Path, pixabay_key: str | None = None) -> pathlib.Path | None:
    """Fetch video from Pixabay (free instant key at https://pixabay.com/api/docs/)."""
    key = pixabay_key or os.environ.get("PIXABAY_API_KEY")
    if not key:
        return None

    query = " ".join(keywords[:2])
    cache_dir.mkdir(parents=True, exist_ok=True)
    target_file = cache_dir / f"pixabay_{abs(hash(query))}.mp4"

    if target_file.exists() and target_file.stat().st_size > 10000:
        return target_file

    try:
        params = {"key": key, "q": query, "per_page": 5}
        resp = requests.get(PIXABAY_SEARCH_URL, params=params, headers=UA, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        hits = data.get("hits", [])
        if not hits:
            return None

        best_url = None
        for hit in hits:
            vids = hit.get("videos", {})
            for size in ("medium", "large", "small", "tiny"):
                if size in vids and vids[size].get("url"):
                    best_url = vids[size]["url"]
                    break
            if best_url:
                break

        if not best_url:
            return None

        with requests.get(best_url, stream=True, headers=UA, timeout=30) as r:
            r.raise_for_status()
            with open(target_file, "wb") as f_out:
                for chunk in r.iter_content(chunk_size=65536):
                    f_out.write(chunk)

        return target_file
    except Exception as ex:
        print(f"Pixabay fetch notice for '{query}': {ex}")
        return None


def fetch_pexels_clip(keywords: list[str], cache_dir: pathlib.Path, pexels_key: str | None = None) -> pathlib.Path | None:
    """Fetch 9:16 vertical video from Pexels API."""
    key = pexels_key or os.environ.get("PEXELS_API_KEY")
    if not key:
        return None

    query = " ".join(keywords[:3])
    cache_dir.mkdir(parents=True, exist_ok=True)
    target_file = cache_dir / f"pexels_{abs(hash(query))}.mp4"

    if target_file.exists() and target_file.stat().st_size > 10000:
        return target_file

    try:
        headers = {"Authorization": key, **UA}
        params = {"query": query, "orientation": "portrait", "per_page": 5}
        resp = requests.get(PEXELS_SEARCH_URL, headers=headers, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        videos = data.get("videos", [])
        if not videos:
            return None

        best_url = None
        for vid in videos:
            files = vid.get("video_files", [])
            for f in files:
                w = f.get("width", 0)
                h = f.get("height", 0)
                if h > w and f.get("link"):
                    best_url = f["link"]
                    break
            if best_url:
                break

        if not best_url:
            return None

        with requests.get(best_url, stream=True, headers=UA, timeout=30) as r:
            r.raise_for_status()
            with open(target_file, "wb") as f_out:
                for chunk in r.iter_content(chunk_size=65536):
                    f_out.write(chunk)

        return target_file
    except Exception as ex:
        print(f"Pexels fetch notice for '{query}': {ex}")
        return None


def fetch_wikimedia_clip(keywords: list[str], cache_dir: pathlib.Path) -> pathlib.Path | None:
    """Fetch video from Wikimedia Commons (100% free, NO API key required)."""
    query = keywords[0] if keywords else "nature"
    cache_dir.mkdir(parents=True, exist_ok=True)
    target_file = cache_dir / f"wikimedia_{abs(hash(query))}.mp4"

    if target_file.exists() and target_file.stat().st_size > 10000:
        return target_file

    try:
        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrnamespace": 6,
            "gsrsearch": f"filetype:video {query}",
            "gsrlimit": 3,
            "prop": "imageinfo",
            "iiprop": "url"
        }
        resp = requests.get(WIKIMEDIA_API_URL, params=params, headers=UA, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        pages = data.get("query", {}).get("pages", {})
        if not pages:
            return None

        video_url = None
        for p in pages.values():
            info = p.get("imageinfo", [{}])[0]
            url = info.get("url")
            if url and (url.endswith(".webm") or url.endswith(".mp4") or url.endswith(".ogv")):
                video_url = url
                break

        if not video_url:
            return None

        with requests.get(video_url, stream=True, headers=UA, timeout=30) as r:
            r.raise_for_status()
            with open(target_file, "wb") as f_out:
                for chunk in r.iter_content(chunk_size=65536):
                    f_out.write(chunk)

        return target_file
    except Exception as ex:
        print(f"Wikimedia fetch notice for '{query}': {ex}")
        return None


def fetch_stock_clip(keywords: list[str], cache_dir: pathlib.Path) -> pathlib.Path | None:
    """Cascade through free video sources: Pixabay -> Pexels -> Wikimedia Commons."""
    clip = fetch_pixabay_clip(keywords, cache_dir)
    if clip:
        return clip

    clip = fetch_pexels_clip(keywords, cache_dir)
    if clip:
        return clip

    clip = fetch_wikimedia_clip(keywords, cache_dir)
    if clip:
        return clip

    return None


def generate_fallback_clip(output_path: pathlib.Path, duration: float, scene_index: int = 0) -> pathlib.Path:
    """Generate an aesthetic, modern 1080x1920 vertical background clip with FFmpeg (no external APIs)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    color = PALETTES[scene_index % len(PALETTES)]

    vf = f"color=c={color}:s=1080x1920:d={duration:.2f}:r=30,vignette=PI/4,format=yuv420p"
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", vf,
        "-t", f"{duration:.2f}",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-an",
        str(output_path)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_path


def prepare_scene_clip(
    raw_video_path: pathlib.Path | None,
    output_path: pathlib.Path,
    duration: float,
    scene_index: int = 0
) -> pathlib.Path:
    """Scale, crop, and normalize a video clip to 1080x1920 @ 30fps with target duration."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not raw_video_path or not raw_video_path.exists():
        return generate_fallback_clip(output_path, duration, scene_index)

    vf = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30"
    cmd = [
        "ffmpeg", "-y",
        "-ss", "0",
        "-i", str(raw_video_path),
        "-t", f"{duration:.2f}",
        "-vf", vf,
        "-c:v", "libx264",
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-an",
        str(output_path)
    ]
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return output_path
    except subprocess.CalledProcessError:
        return generate_fallback_clip(output_path, duration, scene_index)

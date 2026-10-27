"""Image generation module with multi-provider fallback and caching."""
import base64
import hashlib
import logging
import os
import pathlib
import re
import shutil
import time
import urllib.parse
import requests

try:
    from dotenv import load_dotenv
    _env_path = pathlib.Path(__file__).resolve().parent.parent / ".env"
    if _env_path.exists():
        load_dotenv(dotenv_path=_env_path)
except ImportError:
    pass

logger = logging.getLogger(__name__)

TIMEOUT = 45


def sanitize_prompt(raw_prompt: str, art_style: str, char_desc: str, blocked_terms: list[str]) -> str:
    """Build final prompt and strip blocked terms (case-insensitive)."""
    parts = []
    if art_style:
        parts.append(art_style.strip().rstrip("."))
    if char_desc:
        parts.append(char_desc.strip().rstrip("."))
    if raw_prompt:
        parts.append(raw_prompt.strip().rstrip("."))

    combined = ". ".join(parts) + "."

    for term in blocked_terms:
        if not term:
            continue
        # Remove blocked term case-insensitively with boundary/space tolerance
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        combined = pattern.sub("", combined)

    # Clean up double spaces or orphan dots
    combined = re.sub(r"\s+", " ", combined)
    combined = re.sub(r"\.\s*\.", ".", combined).strip()
    return combined


def _generate_cloudflare(prompt: str, seed: int = 42) -> bytes:
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    api_token = os.environ.get("CLOUDFLARE_API_TOKEN")
    if not account_id or not api_token:
        logger.info("Cloudflare credentials not set; skipping provider.")
        raise ValueError("Missing Cloudflare credentials")

    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/black-forest-labs/flux-1-schnell"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": prompt,
        "steps": 4,
        "seed": seed
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=TIMEOUT)
    resp.raise_for_status()

    content_type = resp.headers.get("content-type", "")
    if "application/json" in content_type:
        data = resp.json()
        if "result" in data and isinstance(data["result"], dict) and "image" in data["result"]:
            return base64.b64decode(data["result"]["image"])
        raise RuntimeError(f"Unexpected Cloudflare JSON response: {data}")
    return resp.content


def _generate_together(prompt: str, seed: int = 42) -> bytes:
    api_key = os.environ.get("TOGETHER_API_KEY")
    if not api_key:
        logger.info("Together AI credentials not set; skipping provider.")
        raise ValueError("Missing Together AI credentials")

    url = "https://api.together.xyz/v1/images/generations"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Attempt with FLUX.1-schnell
    models = ["black-forest-labs/FLUX.1-schnell", "black-forest-labs/FLUX.1-schnell-Free"]
    last_err = None

    for model_name in models:
        payload = {
            "model": model_name,
            "prompt": prompt,
            "width": 768,
            "height": 1344,
            "steps": 4,
            "n": 1,
            "seed": seed,
            "response_format": "b64_json"
        }
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            images = data.get("data", [])
            if not images:
                raise RuntimeError("No image data returned from Together AI")
            img_item = images[0]
            if "b64_json" in img_item:
                return base64.b64decode(img_item["b64_json"])
            if "url" in img_item:
                img_resp = requests.get(img_item["url"], timeout=TIMEOUT)
                img_resp.raise_for_status()
                return img_resp.content
        except Exception as ex:
            last_err = ex
            # If 404/400 model name issue, loop to next candidate
            if hasattr(ex, "response") and ex.response is not None and ex.response.status_code in (400, 404):
                continue
            raise

    raise RuntimeError(f"Together AI generation failed on available models: {last_err}")


def _generate_pollinations(prompt: str, seed: int = 42) -> bytes:
    encoded = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width=768&height=1344&nologo=true&seed={seed}&model=flux"
    headers = {"User-Agent": "yt-autopilot/0.2 (personal image bot)"}

    api_key = os.environ.get("POLLINATIONS_API_KEY")
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    resp = requests.get(url, headers=headers, timeout=TIMEOUT)
    resp.raise_for_status()

    content_type = resp.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            err_data = resp.json()
            raise RuntimeError(f"Pollinations returned JSON error: {err_data}")
        except Exception:
            raise RuntimeError(f"Pollinations returned invalid JSON or error payload: {resp.text[:200]}")

    if not resp.content or len(resp.content) < 1000:
        raise RuntimeError("Pollinations returned empty or corrupted image bytes")

    return resp.content


def get_provider_fn(name: str):
    """Dynamically resolve provider function to enable test mocking without network calls."""
    if name == "cloudflare":
        return _generate_cloudflare
    elif name == "together":
        return _generate_together
    elif name == "pollinations":
        return _generate_pollinations
    return None


def generate_image(prompt: str, out_path: pathlib.Path | str, cfg: dict, seed: int = 42) -> str:
    """Generate image for prompt, writing output to out_path and returning provider name."""
    out_file = pathlib.Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    art_style = cfg.get("art_style", "")
    character = cfg.get("character", {})
    char_desc = character.get("description", "")
    blocked_terms = cfg.get("blocked_terms", ["mrbeast", "mr beast"])

    final_prompt = sanitize_prompt(prompt, art_style, char_desc, blocked_terms)

    # Hash caching in tmp/
    prompt_hash = hashlib.sha256(final_prompt.encode("utf-8")).hexdigest()[:16]
    cache_dir = pathlib.Path(__file__).resolve().parent.parent / "tmp" / "image_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cached_img = cache_dir / f"{prompt_hash}.png"
    cached_meta = cache_dir / f"{prompt_hash}.txt"

    if cached_img.exists() and cached_img.stat().st_size > 5000:
        shutil.copyfile(cached_img, out_file)
        prov = cached_meta.read_text().strip() if cached_meta.exists() else "cached"
        logger.info("Loaded cached image for prompt hash %s (provider: %s)", prompt_hash, prov)
        return prov

    requested_providers = cfg.get("image_providers", ["cloudflare", "together", "pollinations"])
    errors = []

    for provider_name in requested_providers:
        provider_fn = get_provider_fn(provider_name)
        if not provider_fn:
            continue

        # Try up to 2 retries with exponential backoff on 429/5xx
        for attempt in range(3):
            try:
                img_bytes = provider_fn(final_prompt, seed=seed)
                if not img_bytes or len(img_bytes) < 1000:
                    raise RuntimeError(f"Provider {provider_name} returned invalid/empty image data")

                # Save to target and cache
                out_file.write_bytes(img_bytes)
                cached_img.write_bytes(img_bytes)
                cached_meta.write_text(provider_name)
                logger.info("Successfully generated image with provider '%s'", provider_name)
                return provider_name
            except ValueError as ex:
                # Missing secret - silently skip
                logger.info("Skipping provider '%s': %s", provider_name, ex)
                break
            except Exception as ex:
                is_retryable = False
                if hasattr(ex, "response") and ex.response is not None:
                    status = ex.response.status_code
                    if status in (429, 500, 502, 503, 504):
                        is_retryable = True
                elif "503" in str(ex) or "429" in str(ex):
                    is_retryable = True

                if is_retryable and attempt < 2:
                    backoff = 2 * (attempt + 1)
                    logger.warning("Provider '%s' error (retryable): %s. Backoff %ss...", provider_name, ex, backoff)
                    time.sleep(backoff)
                    continue

                errors.append(f"{provider_name}: {ex}")
                logger.warning("Provider '%s' failed: %s", provider_name, ex)
                break

    raise RuntimeError(f"All configured image providers failed: {'; '.join(errors)}")

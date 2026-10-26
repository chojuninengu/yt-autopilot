"""Phase 1b - ask a free-tier LLM (Gemini) to pick a trend and plan an ORIGINAL video."""
import json
import os
import pathlib
import requests

# Try to load .env from the project root if available
try:
    from dotenv import load_dotenv
    _env_file = pathlib.Path(__file__).resolve().parent.parent / ".env"
    if _env_file.exists():
        load_dotenv(dotenv_path=_env_file)
except ImportError:
    pass

MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")  # check current free model names
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"

PROMPT = """You are the producer of a faceless short-video channel.
Channel niche: {niche}
Language: {language}
Target length: about {seconds} seconds (vertical 9:16).

Here are today's trending items (JSON):
{items}

Do this:
1. Pick the ONE item with the best viral potential for this niche.
2. Explain the core idea: why is it trending, and what is the underlying hook?
3. Create an ORIGINAL video concept about that idea. Do NOT copy the source's
   text, images, or clips. Use commentary/explanation in your own words.
4. Write the narration script (hook in the first 2 seconds, one clear payoff).
5. Break it into scenes, each with 2-3 generic stock-footage search keywords.

Return ONLY valid JSON with exactly these keys:
{{
  "picked_trend": str,
  "why_viral": str,
  "core_idea": str,
  "video_title": str,
  "script": str,
  "scenes": [{{"narration": str, "visual_keywords": [str]}}],
  "youtube": {{"title": str, "description": str, "hashtags": [str]}},
  "tiktok": {{"caption": str, "hashtags": [str]}}
}}"""


def get_mock_plan(items, cfg):
    """Generate a realistic mock plan for offline local testing without an API key."""
    picked = items[0]["title"] if items else "The Future of AI Automation"
    source = items[0].get("source", "trends") if items else "trends"
    return {
        "picked_trend": f"{picked} (from {source})",
        "why_viral": f"Rapidly gaining massive traction and sparking passionate debate across {source}.",
        "core_idea": f"Behind {picked} is a fundamental shift in how people perceive new technology and internet culture.",
        "video_title": f"The Untold Truth Behind {picked[:35]}",
        "script": (
            f"Why is everyone talking about {picked}? Most people only see the surface headline, "
            "but the real story goes much deeper. When you look closer, this trend reveals exactly "
            "where the digital world is moving next. Here is the one lesson you need to remember: "
            "the simplest ideas often trigger the biggest waves. What do you think about this?"
        ),
        "scenes": [
            {
                "narration": f"Why is everyone talking about {picked}?",
                "visual_keywords": ["smartphone scrolling", "breaking news graphic", "viral social feed"]
            },
            {
                "narration": "Most people only see the surface headline, but the real story goes much deeper.",
                "visual_keywords": ["person thinking deeply", "digital analytics chart", "neon network"]
            },
            {
                "narration": "Here is the one lesson you need to remember: the simplest ideas trigger the biggest waves.",
                "visual_keywords": ["futuristic city timelapse", "light bulb moment", "creator studio setup"]
            }
        ],
        "youtube": {
            "title": f"The Untold Truth Behind {picked[:35]} #shorts",
            "description": f"Breaking down today's top trend ({picked}). Subscribe for daily deep-dives and trend breakdowns!",
            "hashtags": ["trends", "explainer", "technology", "viral", "shorts"]
        },
        "tiktok": {
            "caption": f"What nobody told you about {picked} 🤯 #fyp #trending #explainer",
            "hashtags": ["trending", "explainer", "techtok", "viral", "daily"]
        }
    }


def ideate(items, cfg, mock=False):
    if mock:
        return get_mock_plan(items, cfg)

    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set.\n"
            "To run locally:\n"
            "  1. Set GEMINI_API_KEY in a .env file or export it: export GEMINI_API_KEY='your_key'\n"
            "  2. Or run with --dry-run to test locally without an API key: python src/run_phase1.py --dry-run"
        )
    prompt = PROMPT.format(
        niche=cfg["niche"], language=cfg["language"],
        seconds=cfg["target_seconds"], items=json.dumps(items[:60], ensure_ascii=False))
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.9},
    }
    r = requests.post(URL, headers={"x-goog-api-key": key, "Content-Type": "application/json"},
                      json=body, timeout=90)
    r.raise_for_status()
    text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(text)

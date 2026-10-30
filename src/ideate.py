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

VALID_MOTIONS = ["zoom_in", "zoom_out", "pan_left", "pan_right", "shake"]

PROMPT = """You are the executive producer of a fast-growing, highly credible short-form video channel.
Channel niche: {niche}
Language: {language}
Target length: about {seconds} seconds (vertical 9:16).

Here are today's trending items and breaking headlines (JSON):
{items}

Guidelines:
1. Pick the ONE item with the highest viral potential and immediate relevance to today's news.
2. Maintain strict FACTUAL ACCURACY: Explain the real story truthfully based on the facts. Do NOT hallucinate false claims or misleading stats.
3. Instant Hook: The opening sentence (first 2 seconds) MUST immediately grab attention, provoke curiosity, or highlight the stakes.
4. Voice Pacing: Write narration that flows naturally for text-to-speech. Use clean, punchy sentences. Never use trailing ellipses ("..."). End sentences with clear punctuation (. or ?).
5. Scene Structure: Break into 3-5 punchy scenes. For each scene provide:
   - "narration": crisp, spoken commentary.
   - "visual_keywords": 2-3 generic stock keywords.
   - "image_prompt": vivid 2D cartoon illustration description (Vertical 9:16. Absolutely NO text or letters in the image, NO real people, NO brands. Feature {character_name}: {character_desc} when fitting).
   - "motion": camera motion for this still, exactly one of: "zoom_in", "zoom_out", "pan_left", "pan_right", "shake".

Return ONLY valid JSON with exactly these keys:
{{
  "picked_trend": str,
  "why_viral": str,
  "core_idea": str,
  "video_title": str,
  "script": str,
  "scenes": [
    {{
      "narration": str,
      "visual_keywords": [str],
      "image_prompt": str,
      "motion": str
    }}
  ],
  "youtube": {{"title": str, "description": str, "hashtags": [str]}},
  "tiktok": {{"caption": str, "hashtags": [str]}}
}}"""


def validate_and_sanitize_plan(plan: dict) -> dict:
    """Validate plan structure and ensure safe fallbacks for missing/invalid fields."""
    if not isinstance(plan, dict):
        plan = {}

    plan.setdefault("picked_trend", "Trending Topic")
    plan.setdefault("why_viral", "High interest topic")
    plan.setdefault("core_idea", "Exploration of current trends")
    plan.setdefault("video_title", "Trending Breakdown #shorts")
    plan.setdefault("script", "")

    if "scenes" not in plan or not isinstance(plan["scenes"], list) or len(plan["scenes"]) == 0:
        plan["scenes"] = [
            {
                "narration": plan["script"] or "Today we explore a fascinating trending story.",
                "visual_keywords": ["trending", "technology"],
                "image_prompt": "An expressive cute robot looking curious at glowing holographic data",
                "motion": "zoom_in"
            }
        ]

    for i, scene in enumerate(plan["scenes"]):
        if not isinstance(scene, dict):
            scene = {"narration": str(scene)}
            plan["scenes"][i] = scene

        # Ensure narration
        if not scene.get("narration"):
            scene["narration"] = "Here is what you need to know about this trend."

        # Ensure visual_keywords
        if not scene.get("visual_keywords") or not isinstance(scene["visual_keywords"], list):
            scene["visual_keywords"] = ["technology", "trending"]

        # Ensure image_prompt (default from narration if missing/invalid)
        if not scene.get("image_prompt") or not isinstance(scene["image_prompt"], str) or not scene["image_prompt"].strip():
            scene["image_prompt"] = f"An expressive cartoon scene illustrating: {scene['narration']}"

        # Ensure motion (cycle through VALID_MOTIONS if invalid/missing)
        if scene.get("motion") not in VALID_MOTIONS:
            scene["motion"] = VALID_MOTIONS[i % len(VALID_MOTIONS)]

    # Ensure youtube metadata
    plan.setdefault("youtube", {})
    if not isinstance(plan["youtube"], dict):
        plan["youtube"] = {}
    plan["youtube"].setdefault("title", plan.get("video_title", "Trending Breakdown #shorts"))
    trend_name = plan.get("picked_trend", "today's trend")
    plan["youtube"].setdefault("description", f"Deep dive into {trend_name}!")
    plan["youtube"].setdefault("hashtags", ["shorts", "trending", "tech"])

    # Ensure tiktok metadata
    plan.setdefault("tiktok", {})
    if not isinstance(plan["tiktok"], dict):
        plan["tiktok"] = {}
    plan["tiktok"].setdefault("caption", f"{plan.get('video_title', 'Check this out!')} #shorts")
    plan["tiktok"].setdefault("hashtags", ["shorts", "trending", "tech"])

    return plan


def get_mock_plan(items, cfg):
    """Generate a realistic mock plan for offline local testing without an API key."""
    picked = items[0]["title"] if items else "The Future of AI Automation"
    source = items[0].get("source", "trends") if items else "trends"
    character = cfg.get("character", {})
    name = character.get("name", "Pip")

    plan = {
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
                "visual_keywords": ["smartphone scrolling", "breaking news graphic", "viral social feed"],
                "image_prompt": f"{name} the robot staring wide-eyed at a giant glowing holographic screen displaying viral news",
                "motion": "zoom_in"
            },
            {
                "narration": "Most people only see the surface headline, but the real story goes much deeper.",
                "visual_keywords": ["person thinking deeply", "digital analytics chart", "neon network"],
                "image_prompt": f"{name} the robot scratching its head with glowing antenna, surrounded by intricate floating blueprint schematics",
                "motion": "pan_left"
            },
            {
                "narration": "Here is the one lesson you need to remember: the simplest ideas trigger the biggest waves.",
                "visual_keywords": ["futuristic city timelapse", "light bulb moment", "creator studio setup"],
                "image_prompt": f"{name} the robot raising its hands in celebration against a vibrant futuristic neon city background",
                "motion": "zoom_out"
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
    return validate_and_sanitize_plan(plan)


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
    character = cfg.get("character", {})
    char_name = character.get("name", "our robot mascot Pip")
    char_desc = character.get("description", "A small energetic blue robot with glowing yellow antenna and expressive round eyes")

    prompt = PROMPT.format(
        niche=cfg.get("niche", "tech explainer"),
        language=cfg.get("language", "English"),
        seconds=cfg.get("target_seconds", 40),
        character_name=char_name,
        character_desc=char_desc,
        items=json.dumps(items[:60], ensure_ascii=False)
    )
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.9},
    }
    last_err = None
    for attempt in range(3):
        try:
            r = requests.post(URL, headers={"x-goog-api-key": key, "Content-Type": "application/json"},
                              json=body, timeout=90)
            r.raise_for_status()
            text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            # Handle potential markdown code fences in LLM output
            cleaned_text = text.strip()
            if cleaned_text.startswith("```"):
                lines = cleaned_text.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                cleaned_text = "\n".join(lines).strip()
            plan = json.loads(cleaned_text)
            return validate_and_sanitize_plan(plan)
        except Exception as ex:
            last_err = ex
            import time
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"Gemini ideation failed after 3 attempts: {last_err}")

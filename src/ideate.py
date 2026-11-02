"""Phase 1b - ask a free-tier LLM (Gemini) to pick a trend and plan an ORIGINAL video."""
import json
import os
import pathlib
import re
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

ROOT = pathlib.Path(__file__).resolve().parent.parent
VALID_MOTIONS = ["zoom_in", "zoom_out", "pan_left", "pan_right", "shake"]

PROMPT = """You are the executive producer of a viral curiosity and explainer short-form video channel.
Channel niche: {niche}
Language: {language}
Target length: about {seconds} seconds (vertical 9:16).

STRICT NO-REPEAT POLICY:
The channel recently published videos about these topics:
{recent_topics}

DO NOT PICK ANY OF THE TOPICS LISTED ABOVE OR ANYTHING CLOSELY SIMILAR TO THEM.
Pick a FRESH, mind-bending, highly engaging story from a completely different domain (rotate across: amazing science breakthroughs, strange natural phenomena, ancient archaeology & mysteries, deep sea/space secrets, or bizarre true discoveries).

Here are today's trending items and breaking headlines (JSON):
{items}

Guidelines:
1. Pick ONE story with maximum curiosity and viral intrigue that has NOT been covered recently.
2. Maintain strict FACTUAL ACCURACY: Explain the real story truthfully based on the facts. Do NOT hallucinate false claims or misleading stats.
3. Instant Hook: The opening sentence (first 2 seconds) MUST immediately grab attention, provoke curiosity, or highlight the stakes.
4. Voice Pacing: Write narration that flows naturally for an expressive female narrator (Ava). Use clean, punchy, conversational sentences. Never use trailing ellipses ("..."). End sentences with clear punctuation (. or ?).
5. Scene Structure: Break into 3-5 punchy scenes. For each scene provide:
   - "narration": crisp, spoken commentary.
   - "visual_keywords": 2-3 generic stock keywords.
   - "image_prompt": a visually stunning 3D cinematic scene description (vertical 9:16) capturing the specific setting, subject, and action of this scene (e.g. bioluminescent creatures in deep dark ocean, ancient dusty ruins bathed in golden sunlight, high-tech lab equipment). Describe the actual people, animals, creatures, or environments in the story. Absolutely NO text or letters in the image, NO watermarks, NO brands.
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


def get_recent_topics(out_dir: pathlib.Path, limit: int = 15) -> list[str]:
    """Retrieve list of recently covered topic headlines from past plan files."""
    if not out_dir.exists():
        return []
    candidates = [p for p in out_dir.glob("*-plan.json") if p.name != "latest-plan.json"]
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    recent = []
    for p in candidates[:limit]:
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            topic = d.get("picked_trend") or d.get("video_title")
            if topic and topic not in recent:
                recent.append(topic)
        except Exception:
            continue
    return recent


def filter_unseen_items(items: list[dict], recent_topics: list[str]) -> list[dict]:
    """Deprioritize or filter items that have heavy overlap with recent topics."""
    if not recent_topics:
        return items

    ignore_words = {
        "from", "http", "https", "with", "that", "this", "what", "where", "when",
        "about", "hackernews", "trends", "google", "daily", "video", "shorts",
        "news", "first", "after", "into", "their", "there", "some", "more", "years"
    }
    recent_keywords = set()
    for topic in recent_topics:
        for word in re.findall(r"[A-Za-z0-9]{4,}", topic.lower()):
            if word not in ignore_words:
                recent_keywords.add(word)

    fresh_items = []
    delayed_items = []
    for it in items:
        title_lower = it.get("title", "").lower()
        title_words = set(re.findall(r"[A-Za-z0-9]{4,}", title_lower))
        overlap = title_words & recent_keywords
        if overlap:
            delayed_items.append(it)
        else:
            fresh_items.append(it)

    return fresh_items + delayed_items


def get_mock_plan(items, cfg):
    """Generate a realistic mock plan for offline local testing without an API key."""
    picked = items[0]["title"] if items else "Deep Ocean Bioluminescence Secret"
    source = items[0].get("source", "science_daily") if items else "science_daily"

    plan = {
        "picked_trend": f"{picked} (from {source})",
        "why_viral": f"Rapidly gaining massive traction and sparking curiosity across {source}.",
        "core_idea": f"Behind {picked} is a shocking scientific revelation that defies conventional wisdom.",
        "video_title": f"The Shocking Truth About {picked[:35]}",
        "script": (
            f"Did you know the real story behind {picked}? Most people only see the surface headline, "
            "but what researchers just discovered changes everything. When you look deeper into the evidence, "
            "it reveals a fascinating mystery waiting to be unlocked. What do you think about this?"
        ),
        "scenes": [
            {
                "narration": f"Did you know the real story behind {picked}?",
                "visual_keywords": ["fascinating discovery", "curiosity", "exploration"],
                "image_prompt": "A cinematic wide view of a breathtaking discovery with dramatic golden volumetric lighting and deep atmospheric shadows",
                "motion": "zoom_in"
            },
            {
                "narration": "Most people only see the surface headline, but what researchers just discovered changes everything.",
                "visual_keywords": ["research laboratory", "microscopic view", "unsolved mystery"],
                "image_prompt": "Close-up detailed cinematic shot of glowing particles and ancient intricate artifacts, 3D render style",
                "motion": "pan_left"
            },
            {
                "narration": "When you look deeper into the evidence, it reveals a fascinating mystery waiting to be unlocked.",
                "visual_keywords": ["futuristic observatory", "epic landscape", "discovery payoff"],
                "image_prompt": "An awe-inspiring cinematic landscape under a starry twilight sky with vibrant glowing horizons",
                "motion": "zoom_out"
            }
        ],
        "youtube": {
            "title": f"The Shocking Truth About {picked[:35]} #shorts",
            "description": f"Exploring {picked}. Subscribe for daily mind-bending stories and curiosity breakdowns!",
            "hashtags": ["discovery", "curiosity", "science", "viral", "shorts"]
        },
        "tiktok": {
            "caption": f"What nobody told you about {picked} 🤯 #fyp #trending #curiosity",
            "hashtags": ["discovery", "mindblowing", "curiosity", "viral", "fyp"]
        }
    }
    return validate_and_sanitize_plan(plan)


def ideate(items, cfg, mock=False):
    out_dir = ROOT / "output"
    recent_topics = get_recent_topics(out_dir, limit=15)
    filtered_items = filter_unseen_items(items, recent_topics)

    if mock:
        return get_mock_plan(filtered_items, cfg)

    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set.\n"
            "To run locally:\n"
            "  1. Set GEMINI_API_KEY in a .env file or export it: export GEMINI_API_KEY='your_key'\n"
            "  2. Or run with --dry-run to test locally without an API key: python src/run_phase1.py --dry-run"
        )

    recent_topics_str = "\n".join(f"- {t}" for t in recent_topics) if recent_topics else "None"

    prompt = PROMPT.format(
        niche=cfg.get("niche", "curiosity explainer: fascinating discoveries and viral stories"),
        language=cfg.get("language", "English"),
        seconds=cfg.get("target_seconds", 40),
        recent_topics=recent_topics_str,
        items=json.dumps(filtered_items[:60], ensure_ascii=False)
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

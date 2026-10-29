import os
import json
import re
import requests
from typing import Dict, Any, Optional
from .config import GEMINI_API_KEY

def get_system_prompt(duration_seconds: int = 60) -> str:
    word_count = "240-280 words" if duration_seconds >= 100 else "65-90 words"
    num_scenes = "10 to 14 scenes" if duration_seconds >= 100 else "4 to 6 scenes"
    return f"""You are an elite short-form documentary filmmaker specializing in viral, highly immersive videos (mysteries, deep earth discoveries, astonishing science, ancient secrets).
Create a complete production plan for a {duration_seconds}-second vertical video.

Return ONLY a valid JSON object with the following exact keys:
{{
  "title": "A short, viral, punchy title under 60 chars",
  "topic": "The central mystery or phenomenon",
  "narration": "Full voiceover script, fast-paced, suspenseful, exactly {word_count}",
  "caption": "Viral post description for TikTok & YouTube",
  "hashtags": ["#shorts", "#documentary", "#mystery", "#history", "#viral"],
  "scenes": [
    {{
      "scene_number": 1,
      "narration_fragment": "First sentence of narration",
      "image_prompt": "Ultra-detailed, moving scene description (e.g. sweeping drone flyover, bubbling volcanic crater, rushing deep sea currents, ancient carved megaliths, dramatic atmospheric lighting, 8k cinematic realism, no text)"
    }}
  ]
}}
The video MUST have {num_scenes}. Every image_prompt MUST describe a dynamic moving scene with clear physical actions and environments."""

def generate_story(topic: Optional[str] = None, duration_seconds: int = 60) -> Dict[str, Any]:
    """Generates a viral story and scene plan using Gemini API."""
    if not GEMINI_API_KEY:
        print("[StoryEngine] No GEMINI_API_KEY set, using built-in realistic story template.")
        return FALLBACK_STORY

    prompt = f"Create a viral, suspenseful, realistic documentary story (duration: {duration_seconds}s)."
    if topic:
        prompt = f"Create a viral, suspenseful, realistic documentary story about: '{topic}' (duration: {duration_seconds}s)."

    system_prompt = get_system_prompt(duration_seconds)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": f"{system_prompt}\n\nTask: {prompt}"}]}
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.8
        }
    }

    try:
        res = requests.post(url, json=payload, timeout=30)
        res.raise_for_status()
        data = res.json()
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
        story = json.loads(raw_text)
        print(f"[StoryEngine] Story generated: '{story.get('title')}' with {len(story.get('scenes', []))} scenes.")
        return story
    except Exception as e:
        print(f"[StoryEngine] Warning: Gemini API request failed ({e}). Falling back to template.")
        return FALLBACK_STORY

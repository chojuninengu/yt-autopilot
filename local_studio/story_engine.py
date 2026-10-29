import os
import json
import re
import requests
from typing import Dict, Any, Optional
from .config import GEMINI_API_KEY

SYSTEM_PROMPT = """You are an elite short-form video creator specializing in viral, highly realistic YouTube Shorts and TikToks (mysteries, astonishing science, historical secrets, jaw-dropping facts).
Create a complete production plan for a 30-45 second vertical video.

Return ONLY a valid JSON object with the following exact keys:
{
  "title": "A short, viral, punchy title under 60 chars",
  "topic": "The central mystery or phenomenon",
  "narration": "Full voiceover script, fast-paced, suspenseful, exactly 60-80 words",
  "caption": "Viral post description for TikTok & YouTube",
  "hashtags": ["#shorts", "#mystery", "#didyouknow", "#history", "#viral"],
  "scenes": [
    {
      "scene_number": 1,
      "narration_fragment": "First 1-2 sentences of narration",
      "image_prompt": "Ultra-detailed, photorealistic, 8k, cinematic lighting, national geographic style, dramatic atmosphere, 9:16 aspect ratio framing, highly detailed textures, no text"
    }
  ]
}
Each video MUST have 4 to 6 scenes. Every image_prompt MUST be highly realistic, visually cinematic, and descriptive."""

FALLBACK_STORY = {
    "title": "The Deepest Ocean Mystery Ever Recorded",
    "topic": "Bloop and Deep Ocean Acoustics",
    "narration": "In 1997, underwater microphones thousands of miles apart detected an ultra-low frequency sound from the depths of the Pacific Ocean. Known as The Bloop, it was louder than any known creature on Earth. While scientists later attributed it to massive icequakes fracturing in Antarctica, the deepest trenches of our oceans remain 80% unexplored. What else is down there?",
    "caption": "The loudest sound ever recorded in the ocean was detected thousands of miles away... 🌊 Deep sea mystery.",
    "hashtags": ["#shorts", "#oceanmystery", "#thebloop", "#deepsea", "#unexplained", "#didyouknow"],
    "scenes": [
        {
            "scene_number": 1,
            "narration_fragment": "In 1997, underwater microphones thousands of miles apart detected an ultra-low frequency sound from the depths of the Pacific Ocean.",
            "image_prompt": "Cinematic wide shot of deep dark oceanic trench, dark blue water, glowing underwater hydrophone listening station, realistic atmospheric bioluminescence, 8k photorealistic"
        },
        {
            "scene_number": 2,
            "narration_fragment": "Known as The Bloop, it was louder than any known creature on Earth.",
            "image_prompt": "Mysterious enormous shadowy shape moving slowly through abyssal ocean waters, sonar soundwaves vibrating through water, ultra-detailed photorealistic"
        },
        {
            "scene_number": 3,
            "narration_fragment": "While scientists later attributed it to massive icequakes fracturing in Antarctica, the deepest trenches of our oceans remain 80% unexplored.",
            "image_prompt": "Massive glacial ice shelf cracking in Antarctic ocean, enormous iceberg fracturing under water, cinematic dramatic lighting, National Geographic photography style"
        },
        {
            "scene_number": 4,
            "narration_fragment": "What else is down there?",
            "image_prompt": "Close-up of deep-sea exploration submarine headlights cutting through pitch black water into an unknown underwater abyss, cinematic realism, 8k"
        }
    ]
}

def generate_story(topic: Optional[str] = None) -> Dict[str, Any]:
    """Generates a viral story and scene plan using Gemini API."""
    if not GEMINI_API_KEY:
        print("[StoryEngine] No GEMINI_API_KEY set, using built-in realistic story template.")
        return FALLBACK_STORY

    prompt = "Create a viral, suspenseful, realistic documentary short story."
    if topic:
        prompt = f"Create a viral, suspenseful, realistic documentary short story about: '{topic}'."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": f"{SYSTEM_PROMPT}\n\nTask: {prompt}"}]}
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

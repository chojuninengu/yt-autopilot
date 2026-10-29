import os
import json
import requests
from typing import Dict, Any, Optional
from .config import GEMINI_API_KEY

BATTLE_PROMPT = """You are a master animator and director specializing in viral superhero battle showdowns and dynamic character debates (like Superman vs Metro Man, Goku vs Superman, or two rival animated characters).

Create a high-octane, fast-paced battle script with 4 to 6 alternating lines of punchy dialogue, dramatic actions, sound effects, and impact moments.

Return ONLY a valid JSON object matching this schema:
{
  "title": "Catchy viral battle title under 60 chars",
  "topic": "The showdown subject",
  "caption": "Viral post description with hashtags",
  "hashtags": ["#superman", "#metroman", "#battle", "#vs", "#shorts"],
  "character_1": {
    "name": "Character 1 Name (e.g. Superman)",
    "voice": "en-US-ChristopherNeural",
    "color": "&H00FFFF",
    "visual_theme": "Superman in blue suit with red cape, heroic powerful build, cinematic 3D render style"
  },
  "character_2": {
    "name": "Character 2 Name (e.g. Metro Man)",
    "voice": "en-US-GuyNeural",
    "color": "&HFFFFFF",
    "visual_theme": "Metro Man in brilliant white and gold suit, confident charismatic smirk, cinematic 3D render style"
  },
  "scenes": [
    {
      "scene_number": 1,
      "speaker": 1,
      "dialogue": "Dialogue line for Character 1 (1-2 punchy sentences)",
      "action": "Description of physical action",
      "sfx": "whoosh",
      "shake": false,
      "image_prompt": "Detailed cinematic 3D animation render prompt of Character 1 performing this action, 9:16 framing, highly expressive face, dynamic action camera, 8k, no text"
    },
    {
      "scene_number": 2,
      "speaker": 2,
      "dialogue": "Counter-dialogue line for Character 2",
      "action": "Description of response action",
      "sfx": "whoosh",
      "shake": false,
      "image_prompt": "Detailed cinematic 3D animation render prompt of Character 2 reacting/attacking, 9:16 framing, expressive face, 8k, no text"
    },
    {
      "scene_number": 3,
      "speaker": 1,
      "dialogue": "Heavy attack dialogue",
      "action": "Massive ground strike or punch",
      "sfx": "ground_slam",
      "shake": true,
      "image_prompt": "Epic impact frame of ground exploding with shockwaves, debris flying, 8k cinematic 3D vertical render"
    },
    {
      "scene_number": 4,
      "speaker": 2,
      "dialogue": "Climax response",
      "action": "Energy clash or counter strike",
      "sfx": "punch",
      "shake": true,
      "image_prompt": "Blinding collision of energy between both heroes, dramatic lighting, 8k vertical 9:16"
    }
  ]
}
Available sfx values: 'whoosh', 'punch', 'ground_slam', 'laser'.
Set shake: true on heavy impacts (punches, ground slams, explosions).
"""

FALLBACK_BATTLE = {
  "title": "Superman vs Metro Man: The Ultimate Showdown",
  "topic": "Superman vs Metro Man",
  "caption": "Who wins? Superman or Metro Man? 🔥 Comment your winner below!",
  "hashtags": ["#superman", "#metroman", "#whoisstronger", "#vs", "#shorts"],
  "character_1": {
    "name": "Superman",
    "voice": "en-US-ChristopherNeural",
    "color": "&H00D7FF",
    "visual_theme": "Superman, classic blue suit, red cape, glowing red eyes, heroic build"
  },
  "character_2": {
    "name": "Metro Man",
    "voice": "en-US-GuyNeural",
    "color": "&HFFFFFF",
    "visual_theme": "Metro Man, brilliant white and gold suit, confident smirk, flying at supersonic speed"
  },
  "scenes": [
    {
      "scene_number": 1,
      "speaker": 1,
      "dialogue": "You think speed is your playground, Metro Man? Let's see if you can outrun the Man of Steel!",
      "action": "Superman hovers mid-air with eyes glowing crimson heat-vision",
      "sfx": "whoosh",
      "shake": False,
      "image_prompt": "Cinematic 3D animation style, Superman hovering mid-air, eyes glowing with bright red heat vision, cape billowing dramatically, storm clouds behind, 8k dramatic lighting, vertical 9:16 portrait"
    },
    {
      "scene_number": 2,
      "speaker": 2,
      "dialogue": "Oh Clark, I was moving faster than light before breakfast. You're simply too slow to touch me!",
      "action": "Metro Man effortlessly dodges in a blur of supersonic speed",
      "sfx": "whoosh",
      "shake": False,
      "image_prompt": "Cinematic 3D animation style, Metro Man with a confident dashing smirk, white and gold cape, dodging effortlessly, supersonic shockwave rings expanding around him, 8k vertical 9:16"
    },
    {
      "scene_number": 3,
      "speaker": 1,
      "dialogue": "Then feel the shockwave!",
      "action": "Superman punches the ground causing a massive earthquake crater",
      "sfx": "ground_slam",
      "shake": True,
      "image_prompt": "Cinematic 3D animation style, Superman slamming his fist into the concrete pavement, massive crater exploding with shockwaves and rock fragments, dramatic ground perspective, 8k vertical 9:16"
    },
    {
      "scene_number": 4,
      "speaker": 2,
      "dialogue": "Cute trick, Clark. But a true hero knows how to steal the show!",
      "action": "Metro Man claps with supersonic force creating a blinding shockwave",
      "sfx": "punch",
      "shake": True,
      "image_prompt": "Cinematic 3D animation style, Metro Man clapping his hands together creating a blinding white sonic boom wave pushing against Superman, energy clash explosion, 8k vertical 9:16"
    }
  ]
}

def generate_battle_story(topic: str = "Superman against Metro Man") -> Dict[str, Any]:
    """Generates an action-packed character showdown script with alternating dialogue and SFX."""
    if not GEMINI_API_KEY:
        print("[BattleEngine] No GEMINI_API_KEY set, using built-in battle template.")
        return FALLBACK_BATTLE

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    prompt = f"Create an intense superhero battle showdown with dialogue, sound effects, and ground-shaking impacts for: '{topic}'."
    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": f"{BATTLE_PROMPT}\n\nTask: {prompt}"}]}
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
        plan = json.loads(raw_text)
        print(f"[BattleEngine] Battle generated: '{plan.get('title')}' with {len(plan.get('scenes', []))} turns.")
        return plan
    except Exception as e:
        print(f"[BattleEngine] Warning: Gemini API request failed ({e}), using template.")
        return FALLBACK_BATTLE

import os
import json
import requests
from typing import Dict, Any, Optional
from .config import GEMINI_API_KEY

FABLE_SYSTEM_PROMPT = """You are the master director behind the most viral 3D animated character fables on TikTok and YouTube Shorts (like @heystoriefunny and @pixeltales.ai_).
You specialize in 60-second emotional parables featuring two anthropomorphic 3D Pixar-style characters (e.g. Banana Farmer vs Watermelon Farmer, Little Golden Robot vs Corrupt CEO, or Poor Woodcutter vs Greedy Merchant).

Every story MUST strictly follow this 6-beat viral emotional formula:
Beat 1 (Cruel Injustice): Antagonist hoards a life-or-death resource (water, energy, land) and cruelly mocks the protagonist.
Beat 2 (Despair & Tears): Protagonist on their knees weeping and pleading for a drop of help.
Beat 3 (Determination & Miracle): Protagonist refuses to give up, starts digging in dry barren dirt, and strikes a miraculous fortune (liquid black oil, sparkling crystal gems, or underground geyser)!
Beat 4 (Envious Scheming): Antagonist sees the miracle across the fence, wide-eyed with jealousy, plotting to take it.
Beat 5 (The Fake Apology): Antagonist shamelessly crawls back smiling: 'Forgive me, dear friend! Let's team up to be millionaires!'
Beat 6 (Cold Justice Punchline): Protagonist delivers a chilling, calm moral rejection: 'You let me die of thirst when I begged you.'

Return ONLY a valid JSON object with this exact schema:
{
  "title": "Viral Title under 60 chars (e.g. The Farmer Who Struck Oil)",
  "topic": "Moral theme",
  "caption": "Viral post description with hook",
  "hashtags": ["#animation", "#pixar", "#story", "#karma", "#fable", "#shorts"],
  "character_1": {
    "name": "Antagonist Name (e.g. Watermelon)",
    "description": "Round green striped watermelon head, farmer overalls, smirking expression, 3D Pixar style",
    "voice": "en-US-GuyNeural"
  },
  "character_2": {
    "name": "Protagonist Name (e.g. Banana)",
    "description": "Yellow curved banana head with straw hat, patched denim overalls, highly expressive emotional face, 3D Pixar style",
    "voice": "en-US-ChristopherNeural"
  },
  "scenes": [
    {
      "scene_number": 1,
      "speaker": 1,
      "dialogue": "Antagonist dialogue boasting and denying help (e.g. The canal only flows through my land! If you want water, cry your eyes out!)",
      "emotion": "arrogant",
      "sfx": "whoosh",
      "shake": false,
      "highlight_word": "WATER",
      "image_prompt": "Pixar 3D animation style, cinematic lighting. A lush green farm side-by-side with a bone-dry cracked desert farm. Antagonist smirking arrogantly while Protagonist looks on in dismay, vibrant 3D render, 9:16 vertical composition, 8k, no text"
    },
    {
      "scene_number": 2,
      "speaker": 2,
      "dialogue": "Protagonist pleading desperately (e.g. That's not fair! All my crops are dying, bro! Please give me a drop!)",
      "emotion": "crying",
      "sfx": "tears",
      "shake": false,
      "highlight_word": "PLEASE",
      "image_prompt": "Pixar 3D animation style, close-up dramatic portrait. Protagonist on knees, palms open, big streams of tears pouring from eyes onto parched cracked dirt, heartbreakingly expressive face, 9:16 vertical framing, 8k, no text"
    },
    {
      "scene_number": 3,
      "speaker": 2,
      "dialogue": "Protagonist standing up then gasping at miracle (e.g. That's enough! I won't give up! ...Wait, what is this miracle? It's black oil!)",
      "emotion": "shocked_triumph",
      "sfx": "gushing",
      "shake": true,
      "highlight_word": "OIL",
      "image_prompt": "Pixar 3D animation style, dramatic low-angle hero shot. A roaring fountain of shimmering black oil exploding skyward from a dug hole in the cracked dry ground, Protagonist holding a shovel in pure shock and joy, 9:16 vertical, 8k, no text"
    },
    {
      "scene_number": 4,
      "speaker": 1,
      "dialogue": "Antagonist jealous scheming (e.g. No way this poor sap struck oil on dead dirt! I'm not letting him get rich without me!)",
      "emotion": "envious",
      "sfx": "whoosh",
      "shake": false,
      "highlight_word": "RICH",
      "image_prompt": "Pixar 3D animation style. Antagonist peeking over wooden fence with wide, envious cartoon eyes and greedy grin, clutching his shovel, looking at the gusher in the distance, 9:16 vertical, 8k, no text"
    },
    {
      "scene_number": 5,
      "speaker": 1,
      "dialogue": "Antagonist fake apology (e.g. Forgive me, my dear friend! I was a selfish idiot! Let's team up to become millionaires!)",
      "emotion": "fake_sweet",
      "sfx": "whoosh",
      "shake": false,
      "highlight_word": "FRIEND",
      "image_prompt": "Pixar 3D animation style. Antagonist kneeling with an exaggerated fake innocent smile, offering his hand, while Protagonist stands tall covered in oil barrels, 9:16 vertical, 8k, no text"
    },
    {
      "scene_number": 6,
      "speaker": 2,
      "dialogue": "Cold justice punchline (e.g. You let me die of thirst when I begged you. Get off my land.)",
      "emotion": "cold_rejection",
      "sfx": "punch",
      "shake": true,
      "highlight_word": "NEVER",
      "image_prompt": "Pixar 3D animation style. Protagonist turning his back with cold dignity, golden sunset backlighting, Antagonist left looking pathetic and humbled, cinematic masterpiece, 9:16 vertical, 8k, no text"
    }
  ]
}
"""

FALLBACK_FABLE = {
  "title": "The Banana Farmer Who Struck Oil",
  "topic": "The Karma of the Greedy Farmer",
  "caption": "Karma always hits back harder! 🍌💧 Never look down on someone struggling. #animation #pixar #karma #shorts",
  "hashtags": ["#animation", "#pixar", "#karma", "#story", "#fable", "#shorts"],
  "character_1": {
    "name": "Watermelon",
    "description": "Watermelon farmer with striped round head and overalls",
    "voice": "en-US-GuyNeural"
  },
  "character_2": {
    "name": "Banana",
    "description": "Banana farmer in straw hat and denim overalls",
    "voice": "en-US-ChristopherNeural"
  },
  "scenes": [
    {
      "scene_number": 1,
      "speaker": 1,
      "dialogue": "The irrigation water is only for my cabbage field! If you want water, cry your eyes out and dig your own pond!",
      "emotion": "arrogant",
      "sfx": "whoosh",
      "shake": False,
      "highlight_word": "WATER",
      "image_prompt": "Pixar 3D animation style. A lush green watermelon cabbage patch adjacent to a bone-dry cracked yellow corn field. Watermelon farmer smirking with a trowel, blocking the irrigation trench with red bricks, 9:16 vertical composition, 8k"
    },
    {
      "scene_number": 2,
      "speaker": 2,
      "dialogue": "That's not fair! All my crops are turning to dust, bro! Please, my friend, just give me a little water!",
      "emotion": "crying",
      "sfx": "tears",
      "shake": False,
      "highlight_word": "PLEASE",
      "image_prompt": "Pixar 3D animation style. Banana farmer in straw hat and overalls on his knees, weeping waterfalls of tears from cartoon eyes into his hands onto the parched cracked soil, 9:16 vertical composition, 8k"
    },
    {
      "scene_number": 3,
      "speaker": 2,
      "dialogue": "That's enough! I can't take this injustice anymore! ...Wait! What is this miracle? It's black oil!",
      "emotion": "shocked_triumph",
      "sfx": "gushing",
      "shake": True,
      "highlight_word": "OIL",
      "image_prompt": "Pixar 3D animation style. A massive fountain of sparkling dark crude oil gushing high into the sunny sky from a small hole, Banana farmer holding shovel in astonishment and wild joy, 9:16 vertical composition, 8k"
    },
    {
      "scene_number": 4,
      "speaker": 1,
      "dialogue": "No way this poor sap found oil on dead dirt! There's got to be more under my farm! I'm not letting him get rich without me!",
      "emotion": "envious",
      "sfx": "digging",
      "shake": False,
      "highlight_word": "RICH",
      "image_prompt": "Pixar 3D animation style. Watermelon farmer wildly digging up his own prize cabbages with dirt flying everywhere, crazed greedy expression on his face, 9:16 vertical composition, 8k"
    },
    {
      "scene_number": 5,
      "speaker": 1,
      "dialogue": "Forgive me, my dear friend! I was a selfish idiot! Forget all that, let's team up to become billionaires!",
      "emotion": "fake_sweet",
      "sfx": "whoosh",
      "shake": False,
      "highlight_word": "FRIEND",
      "image_prompt": "Pixar 3D animation style. Watermelon farmer bowing down with an oily fake smile, offering his hand, while Banana farmer stands surrounded by barrels of crude oil, 9:16 vertical composition, 8k"
    },
    {
      "scene_number": 6,
      "speaker": 2,
      "dialogue": "You let me die of thirst when I begged you. Get off my land.",
      "emotion": "cold_rejection",
      "sfx": "punch",
      "shake": True,
      "highlight_word": "NEVER",
      "image_prompt": "Pixar 3D animation style. Banana farmer standing tall with arms crossed and calm confident dignity, golden sunset backlight, Watermelon farmer shrinking away in shame, cinematic 9:16 vertical render, 8k"
    }
  ]
}

def generate_fable_story(topic: Optional[str] = None) -> Dict[str, Any]:
    """Generates a viral 3D character fable matching the exact 5-beat emotional formula."""
    if not GEMINI_API_KEY:
        print("[FableEngine] No GEMINI_API_KEY set, using built-in Banana vs Watermelon fable template.")
        return FALLBACK_FABLE

    prompt = "Create a viral 3D animated character fable about greed, unexpected discovery, and cold karma."
    if topic:
        prompt = f"Create a viral 3D animated character fable about: '{topic}'."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": f"{FABLE_SYSTEM_PROMPT}\n\nTask: {prompt}"}]}
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.85
        }
    }

    try:
        res = requests.post(url, json=payload, timeout=30)
        res.raise_for_status()
        data = res.json()
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
        plan = json.loads(raw_text)
        print(f"[FableEngine] Fable generated: '{plan.get('title')}' with {len(plan.get('scenes', []))} beats.")
        return plan
    except Exception as e:
        print(f"[FableEngine] Gemini call failed ({e}), using template.")
        return FALLBACK_FABLE

import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
STUDIO_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = STUDIO_DIR.parent
OUTPUT_DIR = PROJECT_ROOT / "output" / "local_studio"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Load environment variables
load_dotenv(PROJECT_ROOT / ".env")

# API Keys & Tokens
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
BUFFER_ACCESS_TOKEN = os.getenv("BUFFER_ACCESS_TOKEN", "")
YOUTUBE_TOKEN = os.getenv("YOUTUBE_TOKEN", "")

# Generation Defaults
DEFAULT_VOICE = "en-US-AvaNeural"          # Smooth, warm, engaging female narrator (Microsoft Copilot voice)
DEFAULT_RESOLUTION = (1080, 1920)         # 9:16 Vertical Short / TikTok
DEFAULT_FPS = 30
DEFAULT_SCENE_DURATION = 5                # Seconds per scene
DEFAULT_IMAGE_MODEL = "stabilityai/sd-turbo"  # Fast 1-step local model

# 🎬 Local Studio: High-Speed, $0 Zero-Token AI Video Production Engine

An autonomous local video creation suite designed to produce viral, photorealistic vertical shorts (9:16) for **YouTube Shorts** and **TikTok** in **under 2 minutes per video** at **$0 cost and zero paid tokens**.

---

## ⚡ The Architecture: How It Works in 2 Minutes

```
 🧠 Gemini 2.5 Flash (Free Tier)
        │  Generates viral documentary script & scene prompts
        ▼
 🎨 Visual Engine (Fast FLUX or Local SD-Turbo)
        │  Renders 4-6 photorealistic 8k scenes ($0 tokens)
        ▼
 🎙️ Edge-TTS Neural Voice
        │  Synthesizes studio documentary voiceover + word-timed SRT subtitles (~1s)
        ▼
 🎞️ FFmpeg Cinematic Engine
        │  Dynamic 2.5D Ken Burns camera zoom/pan motion + burned-in glowing subtitles (~10s)
        ▼
 🚀 Automated Multi-Platform Publisher
        ├── YouTube Shorts (Direct API chunked upload)
        └── TikTok (Automated via Buffer GraphQL API)
```

---

## 🚀 Quick Start (One Command)

### 1. Install Requirements
From the project root:
```bash
pip install -r local_studio/requirements.txt
```

### 2. Run Your First Video (Dry Run / Preview)
Generate a full video without uploading to inspect the result:
```bash
python -m local_studio.main --no-publish
```

### 3. Generate & Publish 1 Video
Automatically creates a viral story, generates all images, assembles the video, and publishes to **both YouTube and TikTok**:
```bash
python -m local_studio.main
```

### 4. Batch Mode: Create 25 Videos in a Row! 🔥
Want to generate a batch of videos back-to-back?
```bash
python -m local_studio.main --count 25
```

You can also specify a custom topic:
```bash
python -m local_studio.main --topic "Mysteries of the Mariana Trench"
```

---

## 💡 Image & Video Generation Modes

### Image Generation (`--mode`)
* **`--mode fast` (Default & Recommended):**
  Uses high-speed zero-token cloud rendering (Pollinations FLUX). Generates 1080x1920 vertical photorealistic scenes in ~2-3 seconds per scene. **Zero cost, zero tokens, no GPU needed.**
* **`--mode local`:**
  Runs 100% offline on your local CPU / Intel Arc GPU using `stabilityai/sd-turbo` via Hugging Face `diffusers`. Zero internet connection required for image generation.
* **`--mode auto`:**
  Tries fast endpoint first, seamlessly falls back to offline SD-Turbo if offline.

### Why Cinematic Motion Synthesis instead of Pure AI Diffusion Video?
* **The Reality of Local AI Video Models (SVD, Wan2.1, CogVideoX):**
  Generating a single 3-second 480p clip using AI diffusion video models on a consumer laptop CPU takes **20 to 45 minutes** and requires 24GB+ VRAM. Making 5 scenes would take **over 2 hours per video**.
* **The High-Retention YouTube/TikTok Secret:**
  Top viral creators use **high-resolution photorealistic still frames combined with active 2.5D Ken Burns camera movement (smooth dynamic zoom, pan, tilt, parallax)** + **punchy word-highlighted subtitles**.
  - **Render Time:** **10 seconds** instead of 2 hours!
  - **Resolution:** Full HD **1080x1920** 30fps vertical video.
  - **Cost:** **$0.00**.

---

## ⚙️ CLI Options Reference

| Argument | Options | Description |
| :--- | :--- | :--- |
| `--count` | Integer (e.g. `1`, `5`, `25`) | Number of videos to produce in sequence |
| `--topic` | Text (e.g. `"Ancient Egypt Secrets"`) | Custom topic or let Gemini select viral concepts |
| `--mode` | `fast`, `local`, `auto` | Visual generation engine |
| `--platforms` | `youtube,tiktok`, `youtube`, `tiktok` | Target social channels |
| `--no-publish` | Flag | Preview and save locally without uploading |

---

## 📁 Output Directory
All generated plans, raw audio, scene frames, and final MP4 videos are saved under:
```
output/local_studio/run_<timestamp>/final_video_<timestamp>.mp4
```

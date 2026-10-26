# yt-autopilot

Free, GitHub-Actions-powered pipeline: scout trends -> plan an original video -> render -> publish to YouTube and TikTok.

## Status
- [x] Phase 1: trend scouting + idea/script/caption planning
- [x] Phase 2: render vertical video (edge-tts neural voice + Pexels footage/fallback + styled FFmpeg captions)
- [ ] Phase 3: YouTube upload (private until the free API audit passes)
- [ ] Phase 4: TikTok upload-to-drafts, you tap publish
- [ ] Phase 5: alerts + retries

## Local Testing

You can run and test both Phase 1 and Phase 2 locally:

1. **Install dependencies & FFmpeg:**
   ```bash
   pip install -r requirements.txt
   # Ensure ffmpeg is installed (e.g. sudo apt install ffmpeg on Ubuntu/Debian)
   ```

2. **Phase 1: Scout Trends & Plan:**
   - **Dry run (no API key required):**
     ```bash
     python src/run_phase1.py --dry-run
     ```
   - **Live run (using Gemini API):**
     ```bash
     cp .env.example .env
     # Set GEMINI_API_KEY in .env
     python src/run_phase1.py
     ```
   This generates `output/YYYY-MM-DD-plan.md` and `output/YYYY-MM-DD-plan.json`.

3. **Phase 2: Render Vertical Video:**
   ```bash
   python src/run_phase2.py
   ```
   - Reads the generated plan.
   - Generates neural narration using `edge-tts` (free, zero API key needed).
   - Fetches vertical b-roll footage from Pexels API (or creates clean dark aesthetic motion backgrounds if `PEXELS_API_KEY` is not provided).
   - Burns in bold yellow mobile-optimized subtitles with black outline using FFmpeg.
   - Exports `output/YYYY-MM-DD-video.mp4` (1080x1920 @ 30fps).

4. **Run automated unit tests:**
   ```bash
   python -m unittest discover tests
   ```

## GitHub Actions Setup (Automated Daily Runs)

1. Create a **public** GitHub repository and push this folder.
2. Get a free Gemini API key at [Google AI Studio](https://aistudio.google.com/apikey).
3. (Optional) Get a free Pexels API key at [Pexels API](https://www.pexels.com/api/) for vertical stock footage.
4. In your repo: **Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret**:
   - `GEMINI_API_KEY`: your Gemini key.
   - `PEXELS_API_KEY`: (optional) your Pexels key.
5. In the **Actions** tab on GitHub, click **daily-pipeline** -> **Run workflow** to trigger immediately.
6. The daily plan is committed to git, and the rendered video is available to download under **Artifacts** (`daily-video`).

## Configuration
Edit `config.json` to customize:
- `niche`: channel style and focus
- `voice`: edge-tts voice (e.g. `en-US-ChristopherNeural`, `en-US-AndrewNeural`, `en-US-JennyNeural`)
- `language`: output language
- `target_seconds`: target video duration

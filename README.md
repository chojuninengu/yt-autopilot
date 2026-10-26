# yt-autopilot

Free, GitHub-Actions-powered pipeline: scout trends -> plan an original video -> render -> publish to YouTube and TikTok.

## Status
- [x] Phase 1: trend scouting + idea/script/caption planning
- [x] Phase 2: render vertical video (edge-tts neural voice + Pixabay/Pexels/Wikimedia footage + styled FFmpeg captions)
- [x] Phase 3: YouTube upload (public/private vertical shorts via YouTube Data API v3)
- [x] Phase 4: TikTok upload (upload to Creator Drafts or direct post via TikTok Content Posting API v2)
- [ ] Phase 5: alerts + retries

## Quickstart & Local Testing

You can test every phase locally before scheduling:

1. **Install dependencies & FFmpeg:**
   ```bash
   pip install -r requirements.txt
   # Ensure ffmpeg is installed: sudo apt install ffmpeg
   ```

2. **Phase 1: Scout Trends & Plan Script:**
   ```bash
   # Dry-run test (no API key needed):
   python src/run_phase1.py --dry-run

   # Live run (uses Gemini API):
   python src/run_phase1.py
   ```

3. **Phase 2: Render Vertical Short:**
   ```bash
   python src/run_phase2.py
   ```
   Renders 1080x1920 vertical video (`output/YYYY-MM-DD-video.mp4`) with neural narration, stock footage from Pixabay, and burned-in yellow captions.

4. **Phase 3: YouTube Upload:**
   ```bash
   # Authenticate channel (one-time):
   python src/auth_youtube.py

   # Upload video to YouTube (defaults to public):
   python src/run_phase3.py
   ```

5. **Phase 4: TikTok Upload:**
   ```bash
   # Authenticate TikTok account (one-time):
   python src/auth_tiktok.py

   # Upload to Creator Drafts (recommended - review & post on phone):
   python src/run_phase4.py --mode MEDIA_UPLOAD

   # Or publish directly:
   python src/run_phase4.py --mode DIRECT_POST
   ```

6. **Run test suite:**
   ```bash
   python -m unittest discover tests
   ```

## GitHub Actions Automation (Daily Pipeline)

In your GitHub repository ([`chojuninengu/yt-autopilot`](https://github.com/chojuninengu/yt-autopilot)):
1. Go to **Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret**:
   - `GEMINI_API_KEY`: Your Gemini API key.
   - `PIXABAY_API_KEY`: Your free Pixabay API key.
   - `YOUTUBE_TOKEN`: (Optional) The JSON content of `youtube_token.json` for automated YouTube upload.
   - `TIKTOK_TOKEN`: (Optional) The JSON content of `tiktok_token.json` for automated TikTok upload.
2. Under the **Actions** tab, click **daily-pipeline** -> **Run workflow**.

## Configuration
Edit `config.json` to customize:
- `niche`: channel theme / content style
- `voice`: neural voice (e.g. `en-US-ChristopherNeural`, `en-US-AndrewNeural`)
- `youtube_privacy`: `public` (default), `private`, or `unlisted`
- `language`: output language
- `target_seconds`: target video duration

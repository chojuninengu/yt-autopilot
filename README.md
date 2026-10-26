# yt-autopilot

Free, GitHub-Actions-powered pipeline: scout trends -> plan an original video -> render -> publish to YouTube and TikTok.

## Status
- [x] Phase 1: trend scouting + idea/script/caption planning
- [x] Phase 2: render vertical video (edge-tts neural voice + Pixabay/Pexels/Wikimedia footage + styled FFmpeg captions)
- [x] Phase 3: YouTube upload (upload as private/unlisted shorts via YouTube Data API v3)
- [ ] Phase 4: TikTok upload-to-drafts, you tap publish
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
   - **One-time channel authentication:**
     1. In [Google Cloud Console](https://console.cloud.google.com/apis/credentials?project=gen-lang-client-0742279616), create an OAuth 2.0 Client ID (Application type: **Desktop app**).
     2. Download the JSON and save it as `client_secrets.json` in this project.
     3. Run the authenticator:
        ```bash
        python src/auth_youtube.py
        ```
        This opens your browser to sign in and grants upload permission, generating `youtube_token.json`.
   - **Upload test:**
     ```bash
     # Preview metadata without uploading:
     python src/run_phase3.py --dry-run

     # Upload video as private (safe for testing):
     python src/run_phase3.py --privacy private
     ```

5. **Run test suite:**
   ```bash
   python -m unittest discover tests
   ```

## GitHub Actions Automation (Daily Pipeline)

In your GitHub repository ([`chojuninengu/yt-autopilot`](https://github.com/chojuninengu/yt-autopilot)):
1. Go to **Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret**:
   - `GEMINI_API_KEY`: Your Gemini API key.
   - `PIXABAY_API_KEY`: Your free Pixabay API key.
   - `YOUTUBE_TOKEN`: (Optional) The entire JSON content of `youtube_token.json` for automated daily upload.
2. Under the **Actions** tab, click **daily-pipeline** -> **Run workflow**.

## Configuration
Edit `config.json` to customize:
- `niche`: channel theme / content style
- `voice`: neural voice (e.g. `en-US-ChristopherNeural`, `en-US-AndrewNeural`)
- `language`: output language
- `target_seconds`: target video duration

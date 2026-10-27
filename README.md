# yt-autopilot

Free, GitHub-Actions-powered pipeline: scout trends -> plan an original video -> render -> publish to YouTube and TikTok.

## Status
- [x] Phase 1: trend scouting + idea/script/caption planning
- [x] Phase 2: render vertical video (AI cartoon stills with pan/zoom/shake motion, or stock footage fallback + styled FFmpeg captions)
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
   # Dry-run render with local placeholders (no external image keys needed):
   python src/run_phase2.py --dry-run

   # Live render with AI cartoon stills (or automatic stock fallback):
   python src/run_phase2.py
   ```
   Renders 1080x1920 vertical video (`output/YYYY-MM-DD-video.mp4`) with neural narration, animated 2D cartoon stills, and burned-in yellow captions.

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

## Image Generation Providers ($0 Budget)

The pipeline generates cartoon stills using free image providers in priority order, with automatic stock footage fallback if all fail:

1. **Cloudflare Workers AI (Recommended - Fast & Free):**
   - Model: `@cf/black-forest-labs/flux-1-schnell`
   - Sign up free at [Cloudflare](https://dash.cloudflare.com/).
   - Copy your **Account ID** from *Workers & Pages* -> *Overview*.
   - Create an API token at *My Profile* -> *API Tokens* with *Workers AI Read/Edit* template.
   - Set `CLOUDFLARE_ACCOUNT_ID` and `CLOUDFLARE_API_TOKEN`.

2. **Together AI:**
   - Model: `black-forest-labs/FLUX.1-schnell`
   - Sign up free at [Together AI](https://api.together.ai/) to receive free credits.
   - Copy key from *Settings* -> *API Keys*.
   - Set `TOGETHER_API_KEY`.

3. **Pollinations.ai:**
   - Free and anonymous out-of-the-box (rate-limited to 1 request every 45s per IP).
   - Optional unlimited key from [Pollinations](https://enter.pollinations.ai/) via `POLLINATIONS_API_KEY`.

4. **Stock Footage Fallback:**
   - If no image credentials are set or image generation fails, the pipeline seamlessly falls back to Pixabay/Pexels/Wikimedia stock clips.

## GitHub Actions Automation (Daily Pipeline)

In your GitHub repository ([`chojuninengu/yt-autopilot`](https://github.com/chojuninengu/yt-autopilot)):
1. Go to **Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret**:
   - `GEMINI_API_KEY`: Your Gemini API key.
   - `CLOUDFLARE_ACCOUNT_ID`: (Optional) Cloudflare Account ID for cartoon stills.
   - `CLOUDFLARE_API_TOKEN`: (Optional) Cloudflare API Token for Workers AI.
   - `TOGETHER_API_KEY`: (Optional) Together AI API key.
   - `POLLINATIONS_API_KEY`: (Optional) Pollinations API key.
   - `PIXABAY_API_KEY`: (Optional) Pixabay API key for stock footage fallback.
   - `YOUTUBE_TOKEN`: (Optional) The JSON content of `youtube_token.json` for automated YouTube upload.
   - `TIKTOK_TOKEN`: (Optional) The JSON content of `tiktok_token.json` for automated TikTok upload.
2. Under the **Actions** tab, click **daily-pipeline** -> **Run workflow**.

## Configuration
Edit `config.json` to customize:
- `visual_mode`: `"cartoon_stills"` (default) or `"stock"`
- `art_style`: Style description for cartoon image generation
- `character`: Mascot `name` and `description`
- `image_providers`: Provider order (`["cloudflare", "together", "pollinations"]`)
- `blocked_terms`: Lowercase list of terms to strip from prompts (e.g. real people/brands)
- `disclose_ai_in_description`: Append AI transparency notice to video descriptions
- `niche`: Channel theme / content style
- `voice`: Neural voice (e.g. `en-US-ChristopherNeural`, `en-US-AndrewNeural`)
- `youtube_privacy`: `public` (default), `private`, or `unlisted`

# yt-autopilot

Free, GitHub-Actions-powered pipeline: scout trends -> plan an original video -> (later) render -> publish to YouTube and TikTok.

## Status
- [x] Phase 1: trend scouting + idea/script/caption planning (this repo)
- [ ] Phase 2: render video (edge-tts voice + Pexels footage + FFmpeg captions)
- [ ] Phase 3: YouTube upload (private until the free API audit passes)
- [ ] Phase 4: TikTok upload-to-drafts, you tap publish
- [ ] Phase 5: alerts + retries

## Local Testing

You can run and test this pipeline entirely on your local machine before deploying:

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Dry run (no API key required):**
   Test the entire pipeline end-to-end with simulated LLM generation:
   ```bash
   python src/run_phase1.py --dry-run
   ```
   Check `output/` for the generated `YYYY-MM-DD-plan.md` and `YYYY-MM-DD-plan.json`.

3. **Run automated unit tests:**
   ```bash
   python -m unittest discover tests
   ```

4. **Scout only:**
   Test trend collection across Hacker News, Google Trends, and Reddit:
   ```bash
   python src/run_phase1.py --scout-only
   ```

5. **Live run with Gemini API:**
   - Copy the environment template:
     ```bash
     cp .env.example .env
     ```
   - Add your free Gemini API key to `.env` (`GEMINI_API_KEY=your_key_here`).
   - Run the live pipeline:
     ```bash
     python src/run_phase1.py
     ```

## GitHub Actions Setup (Automated Daily Runs)

1. Create a **public** GitHub repository and push this folder.
2. Get a free Gemini API key at [Google AI Studio](https://aistudio.google.com/apikey).
3. In your repo: **Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret**:
   - Name: `GEMINI_API_KEY`, Value: your API key.
4. **Actions** tab -> `daily-pipeline` -> **Run workflow** to trigger immediately.
5. Check `output/` for `YYYY-MM-DD-plan.md`.

## Notes
- Output is committed to the repo, so plans in `output/` are versioned.
- Scheduled workflows in public repos pause after ~60 days without repository activity; daily commits help maintain activity.
- Reddit may block datacenter IPs; the scout skips failing sources and continues with working sources.
- Set the model with environment variable `GEMINI_MODEL` if you want to customize the model name (defaults to `gemini-2.5-flash`).
- Edit `config.json` to change niche, targets, or language.
- Content rule: make ORIGINAL commentary. Do not re-upload others' memes or clips.

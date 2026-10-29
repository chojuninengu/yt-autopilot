import asyncio
import subprocess
from pathlib import Path
from typing import Tuple
from .config import DEFAULT_VOICE

async def _synthesize_edge_tts(text: str, audio_path: Path, vtt_path: Path, voice: str):
    import edge_tts
    communicate = edge_tts.Communicate(text, voice, rate="+5%")
    sub_maker = edge_tts.SubMaker()
    
    with open(audio_path, "wb") as file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                sub_maker.feed(chunk)

    with open(vtt_path, "w", encoding="utf-8") as file:
        file.write(sub_maker.get_srt())

def generate_voiceover(text: str, work_dir: Path, voice: str = DEFAULT_VOICE) -> Tuple[Path, Path, float]:
    """Generates ultra-realistic voiceover using Edge TTS in ~1 second with word-accurate subtitles.
    Returns: (audio_path, srt_path, duration_seconds)
    """
    work_dir.mkdir(parents=True, exist_ok=True)
    audio_path = work_dir / "voiceover.mp3"
    srt_path = work_dir / "subtitles.srt"

    print(f"[AudioEngine] Synthesizing voiceover with '{voice}'...")
    try:
        asyncio.run(_synthesize_edge_tts(text, audio_path, srt_path, voice))
    except Exception as e:
        print(f"[AudioEngine] Edge TTS async failed ({e}), using gTTS fallback...")
        from gtts import gTTS
        tts = gTTS(text=text, lang="en")
        tts.save(str(audio_path))
        # Empty SRT fallback
        srt_path.write_text("")

    # Determine audio duration via ffprobe
    duration = 30.0
    try:
        cmd = [
            "ffprobe", "-v", "error", "-show_entries",
            "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
            str(audio_path)
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        duration = float(res.stdout.strip())
    except Exception as e:
        print(f"[AudioEngine] ffprobe failed ({e}), estimated duration = {duration}s")

    print(f"[AudioEngine] Audio generated successfully: {duration:.2f}s")
    return audio_path, srt_path, duration

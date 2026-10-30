"""Phase 2a - Generate speech audio and synchronized subtitles with edge-tts."""
import asyncio
import pathlib
import edge_tts

DEFAULT_VOICE = "en-US-ChristopherNeural"
FALLBACK_VOICE = "en-US-GuyNeural"


async def _synthesize(text: str, voice: str, audio_path: pathlib.Path, srt_path: pathlib.Path):
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    srt_path.parent.mkdir(parents=True, exist_ok=True)

    clean_text = text.replace("...", ". ").strip()
    
    for attempt in range(3):
        try:
            target_voice = voice if attempt < 2 else FALLBACK_VOICE
            comm = edge_tts.Communicate(clean_text, target_voice, rate="+2%", pitch="+1Hz")
            submaker = edge_tts.SubMaker()

            with open(audio_path, "wb") as f:
                async for chunk in comm.stream():
                    if chunk["type"] == "audio":
                        f.write(chunk["data"])
                    elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                        submaker.feed(chunk)

            if audio_path.exists() and audio_path.stat().st_size > 500:
                srt_content = submaker.get_srt()
                srt_path.write_text(srt_content, encoding="utf-8")
                return
        except Exception as e:
            if attempt == 2:
                raise e
            await asyncio.sleep(1)


def generate_voiceover(text: str, audio_path: pathlib.Path, srt_path: pathlib.Path, voice: str = DEFAULT_VOICE):
    """Generate audio voiceover and matching SRT subtitle file with clean expressive pacing."""
    asyncio.run(_synthesize(text, voice, audio_path, srt_path))

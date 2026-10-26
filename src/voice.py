"""Phase 2a - Generate speech audio and synchronized subtitles with edge-tts."""
import asyncio
import pathlib
import edge_tts

DEFAULT_VOICE = "en-US-ChristopherNeural"


async def _synthesize(text: str, voice: str, audio_path: pathlib.Path, srt_path: pathlib.Path):
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    srt_path.parent.mkdir(parents=True, exist_ok=True)

    comm = edge_tts.Communicate(text, voice)
    submaker = edge_tts.SubMaker()

    with open(audio_path, "wb") as f:
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] in ("WordBoundary", "SentenceBoundary"):
                submaker.feed(chunk)

    srt_content = submaker.get_srt()
    srt_path.write_text(srt_content, encoding="utf-8")


def generate_voiceover(text: str, audio_path: pathlib.Path, srt_path: pathlib.Path, voice: str = DEFAULT_VOICE):
    """Generate audio voiceover and matching SRT subtitle file."""
    asyncio.run(_synthesize(text, voice, audio_path, srt_path))

import os
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Tuple
from pydub import AudioSegment
import edge_tts
from .fable_sfx import ensure_fable_sfx
from .sfx_generator import ensure_sfx_library

async def _synthesize_voice(text: str, voice: str, rate: str, pitch: str, output_path: Path):
    clean_text = text.replace("...", ". ").strip()
    for attempt in range(3):
        try:
            communicate = edge_tts.Communicate(clean_text, voice, rate=rate, pitch=pitch)
            await communicate.save(str(output_path))
            if output_path.exists() and output_path.stat().st_size > 500:
                return
        except Exception as e:
            if attempt == 2:
                communicate = edge_tts.Communicate(clean_text, "en-US-GuyNeural")
                await communicate.save(str(output_path))
            await asyncio.sleep(1)

VALID_VOICES = {
    "child": ["en-US-AnaNeural", "en-GB-MaisieNeural"],
    "female": ["en-US-AvaNeural", "en-US-JennyNeural", "en-US-EmmaNeural", "en-US-AriaNeural", "en-GB-SoniaNeural", "en-US-MichelleNeural"],
    "male": ["en-US-BrianNeural", "en-US-AndrewNeural", "en-US-GuyNeural", "en-GB-RyanNeural"],
    "elder_boss": ["en-US-EricNeural", "en-US-ChristopherNeural"]
}
ALL_VALID_VOICE_NAMES = [v for group in VALID_VOICES.values() for v in group]

def resolve_character_voice(char: Dict[str, Any], avoid_voice: str = None) -> Tuple[str, str, str]:
    """Intelligently assigns an authentic, diverse character voice (child, woman, man, boss) based on role/description."""
    requested_voice = char.get("voice", "")
    gender = str(char.get("gender", "")).lower()
    text_corpus = f"{char.get('name', '')} {char.get('description', '')} {gender}".lower()

    base_pitch = char.get("pitch", "+0Hz")
    base_rate = char.get("rate", "+0%")

    import re
    tokens = set(re.findall(r"\b[a-z]+\b", text_corpus))

    category = "male"
    # 1. Child / Cute Creature detection
    child_words = {"child", "kid", "baby", "little", "cute", "pup", "cub", "snail", "sprite", "bug", "toddler", "chick"}
    # 2. Female detection
    female_words = {"woman", "female", "lady", "queen", "mother", "girl", "stylist", "princess", "bertha", "she", "her", "mrs", "miss", "sister", "grandma"}
    # 3. Elder / Deep Boss / Monster detection
    elder_words = {"boss", "don", "godfather", "elder", "king", "old", "giant", "monster", "gorilla", "wolf", "deep", "bear", "grandfather", "grandpa"}

    if tokens.intersection(child_words):
        category = "child"
        if base_pitch == "+0Hz":
            base_pitch = "+12Hz"
    elif tokens.intersection(female_words):
        category = "female"
    elif tokens.intersection(elder_words):
        category = "elder_boss"
        if base_pitch == "+0Hz":
            base_pitch = "-6Hz"
    else:
        category = "male"

    candidates = VALID_VOICES[category]

    # If requested_voice is already valid and fits or is distinct, use it
    if requested_voice in ALL_VALID_VOICE_NAMES and requested_voice != avoid_voice:
        chosen_voice = requested_voice
    else:
        # Choose a candidate distinct from avoid_voice
        filtered = [v for v in candidates if v != avoid_voice]
        chosen_voice = filtered[0] if filtered else candidates[0]

    return chosen_voice, base_rate, base_pitch

def render_fable_audio(fable_plan: Dict[str, Any], work_dir: Path) -> Tuple[List[Dict[str, Any]], Path, Path]:
    """Synthesizes high-emotion acting voices for both characters, overlays story SFX, and generates centered viral captions."""
    work_dir.mkdir(parents=True, exist_ok=True)
    fable_sfx = ensure_fable_sfx()
    action_sfx = ensure_sfx_library()
    all_sfx = {**action_sfx, **fable_sfx}

    char1_raw = fable_plan.get("character_1", {"name": "Character 1"})
    char2_raw = fable_plan.get("character_2", {"name": "Character 2"})

    # Intelligently resolve distinct voices for Character 1 and Character 2
    voice1, rate1, pitch1 = resolve_character_voice(char1_raw)
    voice2, rate2, pitch2 = resolve_character_voice(char2_raw, avoid_voice=voice1)

    char1 = {**char1_raw, "voice": voice1, "rate": rate1, "pitch": pitch1}
    char2 = {**char2_raw, "voice": voice2, "rate": rate2, "pitch": pitch2}

    scenes = fable_plan.get("scenes", [])
    scene_audio_meta = []
    combined_audio = AudioSegment.silent(duration=200)

    srt_entries = []
    current_ms = 200

    print(f"[FableAudio] Casting voices: {char1['name']} -> {char1['voice']} ({char1['pitch']}) | {char2['name']} -> {char2['voice']} ({char2['pitch']})")

    for i, scene in enumerate(scenes):
        idx = scene.get("scene_number", i + 1)
        speaker_id = scene.get("speaker", 1)
        speaker = char1 if speaker_id == 1 else char2
        dialogue = scene.get("dialogue", "")
        emotion = scene.get("emotion", "neutral")
        sfx_key = scene.get("sfx", "")
        highlight_word = scene.get("highlight_word", "")

        raw_audio_file = work_dir / f"fable_voice_{idx:02d}.mp3"
        mixed_file = work_dir / f"fable_scene_{idx:02d}.mp3"

        # Emotional pitch and speed tuning layered onto character baseline
        emo = emotion.lower()
        active_rate = speaker.get("rate", "+0%")
        active_pitch = speaker.get("pitch", "+0Hz")

        if "cry" in emo or "whimper" in emo or "helpless" in emo:
            active_rate = "-4%"
            active_pitch = f"{int(active_pitch.replace('Hz','')) + 6:+d}Hz" if "Hz" in active_pitch else "+6Hz"
        elif "arrogant" in emo or "laugh" in emo:
            active_rate = "+6%"
        elif "triumph" in emo or "shock" in emo or "roar" in emo:
            active_rate = "+8%"
            active_pitch = f"{int(active_pitch.replace('Hz','')) + 4:+d}Hz" if "Hz" in active_pitch else "+4Hz"
        elif "cold" in emo or "reject" in emo or "dignity" in emo:
            active_rate = "-6%"
            active_pitch = f"{int(active_pitch.replace('Hz','')) - 4:+d}Hz" if "Hz" in active_pitch else "-4Hz"

        asyncio.run(_synthesize_voice(dialogue, speaker["voice"], active_rate, active_pitch, raw_audio_file))
        speech_seg = AudioSegment.from_file(raw_audio_file)

        # Broadcast-level voice normalization: ensure speech is loud, clear, and perfectly audible (-13.5 dBFS)
        if speech_seg.dBFS != float("-inf"):
            gain_needed = -13.5 - speech_seg.dBFS
            speech_seg = speech_seg.apply_gain(max(min(gain_needed, 14.0), -6.0))

        # Overlay SFX with proper ducking so it never drowns out the dialogue
        matched_sfx = None
        sfx_lower = str(sfx_key).lower()
        for k in all_sfx:
            if k in sfx_lower or sfx_lower in k:
                matched_sfx = k
                break
        if not matched_sfx:
            if "roar" in sfx_lower or "trumpet" in sfx_lower or "slam" in sfx_lower:
                matched_sfx = "ground_slam"
            elif "tear" in sfx_lower or "whimper" in sfx_lower:
                matched_sfx = "tears"
            elif "whoosh" in sfx_lower or "cackle" in sfx_lower or "growl" in sfx_lower:
                matched_sfx = "whoosh"

        if matched_sfx and matched_sfx in all_sfx and all_sfx[matched_sfx].exists():
            sfx_seg = AudioSegment.from_file(all_sfx[matched_sfx])
            # Keep sound effects subordinate to the voice
            if matched_sfx in ["gushing", "ground_slam", "punch"]:
                sfx_seg = sfx_seg - 6
            else:
                sfx_seg = sfx_seg - 12
            mixed_seg = speech_seg.overlay(sfx_seg, position=0)
        else:
            mixed_seg = speech_seg

        # Dramatic pause between beats
        pause_len = 600 if idx in [2, 3, 6] else 400
        mixed_seg = mixed_seg + AudioSegment.silent(duration=pause_len)
        mixed_seg.export(mixed_file, format="mp3")

        seg_duration_ms = len(mixed_seg)
        start_ms = current_ms
        end_ms = current_ms + seg_duration_ms - 200

        def fmt_time(ms):
            s = ms // 1000
            m = s // 60
            h = m // 60
            ms_rem = ms % 1000
            return f"{h:02d}:{m%60:02d}:{s%60:02d},{ms_rem:03d}"

        # Subtitle caption: punchy line with highlight word
        display_caption = dialogue.strip()
        if highlight_word and highlight_word.upper() in display_caption.upper():
            display_caption = display_caption.upper()

        srt_entries.append(
            f"{i+1}\n{fmt_time(start_ms)} --> {fmt_time(end_ms)}\n"
            f"{display_caption}\n"
        )

        combined_audio = combined_audio + mixed_seg
        scene_audio_meta.append({
            "scene_number": idx,
            "speaker": speaker["name"],
            "duration": seg_duration_ms / 1000.0,
            "audio_path": mixed_file,
            "shake": scene.get("shake", False),
            "highlight": highlight_word
        })
        current_ms += seg_duration_ms

    # Master soundtrack normalization to ensure uniform loud, clear broadcast audibility
    if combined_audio.dBFS != float("-inf"):
        master_gain = -13.0 - combined_audio.dBFS
        combined_audio = combined_audio.apply_gain(max(min(master_gain, 6.0), -4.0))

    master_audio_path = work_dir / "fable_soundtrack.mp3"
    combined_audio.export(master_audio_path, format="mp3")

    srt_path = work_dir / "fable_captions.srt"
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_entries))

    print(f"[FableAudio] Fable soundtrack ready: {current_ms/1000:.2f}s with {len(scenes)} narrative beats.")
    return scene_audio_meta, master_audio_path, srt_path

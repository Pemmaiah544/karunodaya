"""
Speech Recognition Service

Uses OpenAI Whisper (via HuggingFace transformers) for server-side
speech-to-text transcription and provides transcript-vs-passage
comparison for the fluency check reading assessment.
"""
import os
import re
import uuid
import logging
import subprocess
from pathlib import Path

from django.conf import settings
import imageio_ffmpeg

_FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

logger = logging.getLogger(__name__)

# ── Singleton Model Loader ──────────────────────────────────────────

_pipeline = None

LANG_MAP = {
    'EN': 'english',
    'HI': 'hindi',
    'KN': 'kannada',
    'TA': 'tamil',
    'TE': 'telugu',
    'ML': 'malayalam',
    'BN': 'bengali',
    'MR': 'marathi',
    'GU': 'gujarati',
    'PA': 'punjabi',
    'OR': 'odia',
    'AS': 'assamese',
    'UR': 'urdu',
}


def _get_pipeline():
    """Lazy-load the ASR pipeline (singleton). First call downloads ~244MB model."""
    global _pipeline
    if _pipeline is None:
        logger.info("Loading Whisper model (first call may download ~244MB)...")
        from transformers import pipeline as hf_pipeline
        _pipeline = hf_pipeline(
            "automatic-speech-recognition",
            model="openai/whisper-small",
            device=-1,  # CPU
        )
        logger.info("Whisper model loaded successfully.")
    return _pipeline


# ── Audio Processing ────────────────────────────────────────────────

def _save_uploaded_audio(uploaded_file):
    """Save an InMemoryUploadedFile to a temporary path. Returns path string."""
    upload_dir = Path(settings.MEDIA_ROOT) / 'fluency_audio'
    upload_dir.mkdir(parents=True, exist_ok=True)

    ext = uploaded_file.name.rsplit('.', 1)[-1] if '.' in uploaded_file.name else 'webm'
    filename = f"{uuid.uuid4().hex}.{ext}"
    file_path = str(upload_dir / filename)

    with open(file_path, 'wb') as f:
        for chunk in uploaded_file.chunks():
            f.write(chunk)
    return file_path


def _convert_to_wav(audio_file_path):
    """Convert any audio format (WebM, OGG, MP4) to 16kHz mono WAV using ffmpeg directly."""
    wav_path = audio_file_path.rsplit('.', 1)[0] + '.wav'
    try:
        result = subprocess.run(
            [_FFMPEG, '-y', '-i', audio_file_path, '-ar', '16000', '-ac', '1', '-f', 'wav', wav_path],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            logger.error(f"ffmpeg stderr: {result.stderr[:500]}")
            raise RuntimeError(f"ffmpeg failed with code {result.returncode}")
        return wav_path
    except subprocess.TimeoutExpired:
        raise ValueError("Audio conversion timed out")
    except Exception as e:
        logger.error(f"Audio conversion failed: {e}")
        raise ValueError(f"Could not process audio file: {e}")


def cleanup_audio_files(*paths):
    """Delete temporary audio files after processing."""
    for p in paths:
        try:
            if p and os.path.exists(p):
                os.remove(p)
        except OSError as e:
            logger.warning(f"Could not remove temp file {p}: {e}")


# ── Transcription ───────────────────────────────────────────────────

def transcribe(audio_file_path, language='EN'):
    """
    Transcribe audio file using Whisper.

    Args:
        audio_file_path: Path to audio file (any format supported by ffmpeg)
        language: Language code ('EN', 'HI', 'KN', etc.)

    Returns:
        str: Transcribed text

    Raises:
        ValueError: If audio cannot be processed
        RuntimeError: If model fails
    """
    import soundfile as sf
    import numpy as np

    wav_path = None
    try:
        wav_path = _convert_to_wav(audio_file_path)

        # Load WAV as numpy array to bypass the pipeline's internal ffmpeg dependency
        audio_data, sample_rate = sf.read(wav_path, dtype='float32')
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)

        pipe = _get_pipeline()

        generate_kwargs = {
            "language": LANG_MAP.get(language, 'english'),
            "task": "transcribe",
        }

        # Pass raw audio dict instead of file path
        result = pipe(
            {"raw": audio_data, "sampling_rate": sample_rate},
            generate_kwargs=generate_kwargs,
            chunk_length_s=30,
            batch_size=1,
        )

        transcript = result.get("text", "").strip()
        logger.info(f"Transcription done: {len(transcript)} chars, lang={language}")
        return transcript

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise RuntimeError(f"Speech recognition failed: {e}")
    finally:
        if wav_path and wav_path != audio_file_path:
            cleanup_audio_files(wav_path)


# ── Transcript vs Passage Comparison ────────────────────────────────

PUNCTUATION_RE = re.compile(r'[.,!?;:"\'\u201C\u201D\u2018\u2019\-]')

MAX_LOOK_AHEAD = 6
SHORT_WORD_THRESHOLD = 3
SHORT_WORD_MAX_AHEAD = 2


def _clean_word(word):
    """Normalize a word: lowercase, strip punctuation."""
    return PUNCTUATION_RE.sub('', word.lower()).strip()


def _levenshtein(a, b):
    """Compute Levenshtein edit distance between two strings."""
    if len(a) < len(b):
        return _levenshtein(b, a)
    if len(b) == 0:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr = [i + 1]
        for j, cb in enumerate(b):
            cost = 0 if ca == cb else 1
            curr.append(min(curr[j] + 1, prev[j + 1] + 1, prev[j] + cost))
        prev = curr
    return prev[-1]


def _lenient_match(target, spoken):
    """Lenient fuzzy match — used for the immediate next word (position 0)."""
    if target == spoken:
        return True
    if len(target) <= 2:
        return spoken == target
    if len(target) == 3 and len(spoken) >= 2:
        return _levenshtein(target, spoken) <= 1
    if abs(len(target) - len(spoken)) > 3:
        return False
    if len(spoken) >= 3 and target.startswith(spoken):
        return True
    if len(target) >= 3 and spoken.startswith(target):
        return True
    max_dist = 1 if len(target) <= 5 else 2
    return len(spoken) >= 2 and _levenshtein(target, spoken) <= max_dist


def _strict_match(target, spoken):
    """Strict fuzzy match — used for look-ahead positions 1+ (prevents false jumps)."""
    if target == spoken:
        return True
    if len(target) <= 3 or len(spoken) <= 2:
        return False
    if abs(len(target) - len(spoken)) > 2:
        return False
    shorter = min(len(target), len(spoken))
    longer = max(len(target), len(spoken))
    if shorter >= 4 and shorter / longer >= 0.8:
        if target.startswith(spoken) or spoken.startswith(target):
            return True
    max_dist = 1 if len(target) <= 5 else 2
    return _levenshtein(target, spoken) <= max_dist


def compare_transcript_to_passage(transcript_text, passage_text):
    """
    Compare ASR transcript against the expected passage text.

    Uses a forward-matching algorithm (ported from the JS tryMatch logic):
    walk through passage words sequentially, for each transcript word try
    to match within a look-ahead window, then try backward recovery for
    previously skipped words.

    Returns:
        dict with words_read, total_words, accuracy, missed_words
    """
    passage_words = passage_text.strip().split()
    passage_clean = [_clean_word(w) for w in passage_words]

    transcript_words = transcript_text.strip().split()
    transcript_clean = [_clean_word(w) for w in transcript_words]

    current_pos = 0
    matched = set()
    skipped = set()

    for spoken in transcript_clean:
        if not spoken:
            continue

        found = False

        # Forward look-ahead from current position
        for j in range(MAX_LOOK_AHEAD):
            target_idx = current_pos + j
            if target_idx >= len(passage_clean):
                break
            if len(spoken) <= SHORT_WORD_THRESHOLD and j > SHORT_WORD_MAX_AHEAD:
                break

            is_match = (_lenient_match(passage_clean[target_idx], spoken) if j == 0
                        else _strict_match(passage_clean[target_idx], spoken))

            if is_match:
                for s in range(current_pos, target_idx):
                    if s not in matched:
                        skipped.add(s)
                matched.add(target_idx)
                skipped.discard(target_idx)
                current_pos = target_idx + 1
                found = True
                break

        # Backward recovery: try to match previously skipped words
        if not found:
            for idx in list(skipped):
                if _lenient_match(passage_clean[idx], spoken):
                    matched.add(idx)
                    skipped.discard(idx)
                    break

    # Words before current_pos that weren't matched are "missed"
    missed_words = [passage_words[i] for i in sorted(skipped) if i < current_pos]

    words_read = len(matched)
    total_words = len(passage_words)
    accuracy = round((words_read / total_words) * 100) if total_words > 0 else 0
    accuracy = min(accuracy, 100)

    return {
        'words_read': words_read,
        'total_words': total_words,
        'accuracy': accuracy,
        'missed_words': missed_words,
        'matched_indices': sorted(matched),
    }

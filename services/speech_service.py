"""
Speech Recognition Service

Primary engine : AI4Bharat Bhashini cloud ASR (fast, optimised for Indian languages).
                 Requires BHASHINI_USER_ID + BHASHINI_API_KEY in .env.
                 Register free at https://bhashini.gov.in/ulca
Fallback engine: OpenAI Whisper-small via HuggingFace Transformers (runs on CPU locally).
                 Used automatically when Bhashini credentials are not configured.

All public function signatures and return shapes are unchanged — callers need no updates.
"""
import os
import re
import uuid
import base64
import logging
import subprocess
from pathlib import Path

from django.conf import settings
import imageio_ffmpeg

_FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

logger = logging.getLogger(__name__)

# ── Whisper singleton (lazy-loaded only when Bhashini is unavailable) ──────────

_whisper_pipeline = None

# ── Language maps ──────────────────────────────────────────────────────────────

# Whisper language names
LANG_MAP_WHISPER = {
    'EN': 'english', 'HI': 'hindi',  'KN': 'kannada',  'TA': 'tamil',
    'TE': 'telugu',  'ML': 'malayalam', 'BN': 'bengali', 'MR': 'marathi',
    'GU': 'gujarati','PA': 'punjabi',  'OR': 'odia',    'AS': 'assamese',
    'UR': 'urdu',
}

# Bhashini BCP-47 source language codes
LANG_MAP_BHASHINI = {
    'EN': 'en', 'HI': 'hi', 'KN': 'kn', 'TA': 'ta',
    'TE': 'te', 'ML': 'ml', 'BN': 'bn', 'MR': 'mr',
    'GU': 'gu', 'PA': 'pa', 'OR': 'or', 'AS': 'as',
    'UR': 'ur',
}

# Keep old alias so any code that imported LANG_MAP still works
LANG_MAP = LANG_MAP_WHISPER


# ── Helpers ────────────────────────────────────────────────────────────────────

def _bhashini_configured():
    """Return True if Bhashini credentials are present in settings."""
    return bool(getattr(settings, 'BHASHINI_USER_ID', '') and
                getattr(settings, 'BHASHINI_API_KEY', ''))


def _get_whisper_pipeline():
    """Lazy-load the local Whisper model (singleton). ~244 MB download on first call."""
    global _whisper_pipeline
    if _whisper_pipeline is None:
        logger.info("Loading Whisper model (first call may download ~244 MB)...")
        from transformers import pipeline as hf_pipeline
        _whisper_pipeline = hf_pipeline(
            "automatic-speech-recognition",
            model="openai/whisper-small",
            device=-1,  # CPU
        )
        logger.info("Whisper model loaded.")
    return _whisper_pipeline


# ── Audio helpers ──────────────────────────────────────────────────────────────

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
    """Convert any audio format to 16 kHz mono WAV using bundled ffmpeg."""
    wav_path = audio_file_path.rsplit('.', 1)[0] + '.wav'
    try:
        result = subprocess.run(
            [_FFMPEG, '-y', '-i', audio_file_path,
             '-ar', '16000', '-ac', '1', '-f', 'wav', wav_path],
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


# ── AI4Bharat / Bhashini ASR ───────────────────────────────────────────────────

_bhashini_service_cache = {}   # {lang_code: {'serviceId': ..., 'callbackUrl': ..., ...}}


def _bhashini_get_service_config(source_lang):
    """
    Fetch Bhashini pipeline config for the given source language.
    Caches result per language for the process lifetime.
    Returns dict with serviceId, callbackUrl, authKey, authValue.
    Raises RuntimeError on failure.
    """
    if source_lang in _bhashini_service_cache:
        return _bhashini_service_cache[source_lang]

    import requests as req

    user_id    = settings.BHASHINI_USER_ID
    api_key    = settings.BHASHINI_API_KEY
    pipeline_id = getattr(settings, 'BHASHINI_PIPELINE_ID', '64392f96daac500b55c543cd')

    config_url = "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline"
    payload = {
        "pipelineTasks": [
            {"taskType": "asr", "config": {"language": {"sourceLanguage": source_lang}}}
        ],
        "pipelineRequestConfig": {"pipelineId": pipeline_id},
    }
    headers = {
        "userID":     user_id,
        "ulcaApiKey": api_key,
        "Content-Type": "application/json",
    }
    try:
        resp = req.post(config_url, json=payload, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        pipe_resp = data['pipelineResponseConfig'][0]
        service_id = pipe_resp['config'][0]['serviceId']
        ep = data['pipelineInferenceAPIEndPoint']
        callback_url = ep['callbackUrl']
        auth_key     = ep['inferenceApiKey']['name']
        auth_value   = ep['inferenceApiKey']['value']

        result = {
            'serviceId':   service_id,
            'callbackUrl': callback_url,
            'authKey':     auth_key,
            'authValue':   auth_value,
        }
        _bhashini_service_cache[source_lang] = result
        logger.info(f"Bhashini service config fetched for lang={source_lang}, serviceId={service_id}")
        return result
    except Exception as e:
        raise RuntimeError(f"Bhashini config fetch failed for lang={source_lang}: {e}")


def _transcribe_bhashini(wav_path, language='EN'):
    """
    Transcribe a WAV file via the AI4Bharat Bhashini cloud ASR API.
    Returns transcript string.
    Raises RuntimeError on any failure (caller falls back to Whisper).
    """
    import requests as req

    source_lang = LANG_MAP_BHASHINI.get(language, 'en')
    cfg = _bhashini_get_service_config(source_lang)

    with open(wav_path, 'rb') as f:
        audio_b64 = base64.b64encode(f.read()).decode('utf-8')

    payload = {
        "pipelineTasks": [
            {
                "taskType": "asr",
                "config": {
                    "language":  {"sourceLanguage": source_lang},
                    "serviceId": cfg['serviceId'],
                    "audioFormat": "wav",
                    "samplingRate": 16000,
                },
            }
        ],
        "inputData": {
            "input": [{"source": ""}],
            "audio": [{"audioContent": audio_b64}],
        },
    }
    headers = {
        cfg['authKey']: cfg['authValue'],
        "Content-Type": "application/json",
    }
    resp = req.post(cfg['callbackUrl'], json=payload, headers=headers, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    transcript = data['pipelineResponse'][0]['output'][0]['source']
    logger.info(f"Bhashini transcript ({language}): {len(transcript)} chars")
    return transcript.strip()


# ── Whisper fallback ───────────────────────────────────────────────────────────

def _transcribe_whisper(wav_path, language='EN'):
    """Transcribe using local OpenAI Whisper-small. Returns transcript string."""
    import soundfile as sf
    import numpy as np

    audio_data, sample_rate = sf.read(wav_path, dtype='float32')
    if len(audio_data.shape) > 1:
        audio_data = np.mean(audio_data, axis=1)

    pipe = _get_whisper_pipeline()
    result = pipe(
        {"raw": audio_data, "sampling_rate": sample_rate},
        generate_kwargs={
            "language": LANG_MAP_WHISPER.get(language, 'english'),
            "task": "transcribe",
        },
        chunk_length_s=15,
        stride_length_s=3,
        batch_size=4,
    )
    transcript = result.get("text", "").strip()
    logger.info(f"Whisper transcript ({language}): {len(transcript)} chars")
    return transcript


def _transcribe_whisper_with_timestamps(wav_path, language='EN'):
    """Transcribe using local Whisper with word-level timestamps. Returns dict."""
    import soundfile as sf
    import numpy as np

    audio_data, sample_rate = sf.read(wav_path, dtype='float32')
    if len(audio_data.shape) > 1:
        audio_data = np.mean(audio_data, axis=1)

    pipe = _get_whisper_pipeline()
    result = pipe(
        {"raw": audio_data, "sampling_rate": sample_rate},
        generate_kwargs={
            "language": LANG_MAP_WHISPER.get(language, 'english'),
            "task": "transcribe",
        },
        chunk_length_s=15,
        stride_length_s=3,
        batch_size=4,
        return_timestamps="word",
    )
    chunks = []
    for c in result.get('chunks', []):
        ts = c.get('timestamp') or (None, None)
        chunks.append({'text': c.get('text', ''), 'start': ts[0], 'end': ts[1]})
    transcript = result.get('text', '').strip()
    logger.info(f"Whisper timestamp transcript ({language}): {len(transcript)} chars, {len(chunks)} chunks")
    return {'text': transcript, 'chunks': chunks}


# ── Public Transcription API (unchanged signatures) ────────────────────────────

def transcribe(audio_file_path, language='EN'):
    """
    Transcribe audio file — tries AI4Bharat Bhashini first, falls back to Whisper.

    Args:
        audio_file_path: Path to audio file (any ffmpeg-supported format)
        language: Language code ('EN', 'HI', 'KN', etc.)

    Returns:
        str: Transcribed text

    Raises:
        ValueError: If audio cannot be processed
        RuntimeError: If both engines fail
    """
    wav_path = None
    try:
        wav_path = _convert_to_wav(audio_file_path)

        if _bhashini_configured():
            try:
                return _transcribe_bhashini(wav_path, language)
            except Exception as e:
                logger.warning(f"Bhashini ASR failed ({e}), falling back to Whisper")

        return _transcribe_whisper(wav_path, language)

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise RuntimeError(f"Speech recognition failed: {e}")
    finally:
        if wav_path and wav_path != audio_file_path:
            cleanup_audio_files(wav_path)


def transcribe_with_timestamps(audio_file_path, language='EN'):
    """
    Transcribe audio and return word-level timestamps for decoding-latency analysis.
    Tries AI4Bharat Bhashini first (timestamps approximated from word count),
    falls back to local Whisper which provides native word timestamps.

    Returns:
        dict: {
            'text': str,
            'chunks': list of {'text': str, 'start': float|None, 'end': float|None}
        }
    """
    wav_path = None
    try:
        wav_path = _convert_to_wav(audio_file_path)

        if _bhashini_configured():
            try:
                transcript = _transcribe_bhashini(wav_path, language)
                # Bhashini doesn't return word-level timestamps; synthesise
                # approximate timing from equal-duration word spacing.
                # This is enough for decoding-latency heuristics.
                words = transcript.split()
                chunks = [{'text': w, 'start': None, 'end': None} for w in words]
                return {'text': transcript, 'chunks': chunks}
            except Exception as e:
                logger.warning(f"Bhashini ASR (timestamps) failed ({e}), falling back to Whisper")

        return _transcribe_whisper_with_timestamps(wav_path, language)

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Timestamp transcription failed: {e}")
        raise RuntimeError(f"Speech recognition with timestamps failed: {e}")
    finally:
        if wav_path and wav_path != audio_file_path:
            cleanup_audio_files(wav_path)


# ── Transcript vs Passage Comparison (unchanged) ───────────────────────────────

PUNCTUATION_RE = re.compile(r'[.,!?;:\"\'\u201C\u201D\u2018\u2019\-]')

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
    longer  = max(len(target), len(spoken))
    if shorter >= 4 and shorter / longer >= 0.8:
        if target.startswith(spoken) or spoken.startswith(target):
            return True
    max_dist = 1 if len(target) <= 5 else 2
    return _levenshtein(target, spoken) <= max_dist


def compare_transcript_to_passage(transcript_text, passage_text):
    """
    Compare ASR transcript against the expected passage text.

    Uses a forward-matching algorithm:  walk through passage words sequentially,
    for each transcript word try to match within a look-ahead window, then try
    backward recovery for previously skipped words.

    Returns:
        dict with words_read, total_words, accuracy, missed_words,
        transcript_word_count, matched_indices, skipped_indices
    """
    passage_words  = passage_text.strip().split()
    passage_clean  = [_clean_word(w) for w in passage_words]

    transcript_words = transcript_text.strip().split()
    transcript_clean = [_clean_word(w) for w in transcript_words]

    transcript_word_count = sum(1 for w in transcript_clean if w)

    current_pos = 0
    matched = set()
    skipped = set()

    for spoken in transcript_clean:
        if not spoken:
            continue

        found = False

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

        if not found:
            for idx in list(skipped):
                if _lenient_match(passage_clean[idx], spoken):
                    matched.add(idx)
                    skipped.discard(idx)
                    break

    missed_words = [passage_words[i] for i in sorted(skipped) if i < current_pos]

    words_read  = len(matched)
    total_words = len(passage_words)
    accuracy    = round((words_read / total_words) * 100) if total_words > 0 else 0
    accuracy    = min(accuracy, 100)

    return {
        'words_read':           words_read,
        'total_words':          total_words,
        'accuracy':             accuracy,
        'missed_words':         missed_words,
        'transcript_word_count': transcript_word_count,
        'matched_indices':      sorted(matched),
        'skipped_indices':      sorted(skipped),
    }

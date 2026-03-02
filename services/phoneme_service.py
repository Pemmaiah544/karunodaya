"""
Phoneme & Miscue Analysis Service

Analyses ASR transcript vs reference passage to detect:
- Phonetic weaknesses (specific sound/pattern errors)
- Miscue types: NONSENSE (poor phonics) | SEMANTIC (context guessing) | VISUAL (shape confusion)
- Reading style: GUESSR (meaning-driven) | DECODER (phonics-driven, slow)
- Decoding latency: inter-word pause durations for short words

No external ML or phoneme libraries required — uses inline pattern matching.
"""
import re
import logging

logger = logging.getLogger(__name__)

# ── English phoneme cluster patterns ──────────────────────────────────────────
# Covers digraphs, blends, and short vowel CVC patterns most relevant to ages 3–8.
# Each key is the "phoneme label" stored in child.phonetic_weaknesses.
PHONEME_PATTERNS = {
    'th': re.compile(r'\bth\w*|\w*th\b', re.IGNORECASE),
    'sh': re.compile(r'\bsh\w*|\w*sh\b', re.IGNORECASE),
    'ch': re.compile(r'\bch\w*|\w*ch\b', re.IGNORECASE),
    'wh': re.compile(r'\bwh\w*', re.IGNORECASE),
    'ph': re.compile(r'\bph\w*|\w*ph\b', re.IGNORECASE),
    'qu': re.compile(r'\bqu\w*', re.IGNORECASE),
    'ing': re.compile(r'\w+ing\b', re.IGNORECASE),
    'tion': re.compile(r'\w+tion\b', re.IGNORECASE),
    'ck': re.compile(r'\w+ck\b', re.IGNORECASE),
    'bl': re.compile(r'\bbl\w+', re.IGNORECASE),
    'br': re.compile(r'\bbr\w+', re.IGNORECASE),
    'cl': re.compile(r'\bcl\w+', re.IGNORECASE),
    'cr': re.compile(r'\bcr\w+', re.IGNORECASE),
    'dr': re.compile(r'\bdr\w+', re.IGNORECASE),
    'fl': re.compile(r'\bfl\w+', re.IGNORECASE),
    'fr': re.compile(r'\bfr\w+', re.IGNORECASE),
    'gl': re.compile(r'\bgl\w+', re.IGNORECASE),
    'gr': re.compile(r'\bgr\w+', re.IGNORECASE),
    'pl': re.compile(r'\bpl\w+', re.IGNORECASE),
    'pr': re.compile(r'\bpr\w+', re.IGNORECASE),
    'sl': re.compile(r'\bsl\w+', re.IGNORECASE),
    'sm': re.compile(r'\bsm\w+', re.IGNORECASE),
    'sn': re.compile(r'\bsn\w+', re.IGNORECASE),
    'sp': re.compile(r'\bsp\w+', re.IGNORECASE),
    'st': re.compile(r'\bst\w+|\w+st\b', re.IGNORECASE),
    'str': re.compile(r'\bstr\w+', re.IGNORECASE),
    'sw': re.compile(r'\bsw\w+', re.IGNORECASE),
    'tr': re.compile(r'\btr\w+', re.IGNORECASE),
    'short_a': re.compile(r'\b[b-df-hj-np-tv-z]a[b-df-hj-np-tv-z]\b', re.IGNORECASE),
    'short_e': re.compile(r'\b[b-df-hj-np-tv-z]e[b-df-hj-np-tv-z]\b', re.IGNORECASE),
    'short_i': re.compile(r'\b[b-df-hj-np-tv-z]i[b-df-hj-np-tv-z]\b', re.IGNORECASE),
    'short_o': re.compile(r'\b[b-df-hj-np-tv-z]o[b-df-hj-np-tv-z]\b', re.IGNORECASE),
    'short_u': re.compile(r'\b[b-df-hj-np-tv-z]u[b-df-hj-np-tv-z]\b', re.IGNORECASE),
}

# ── Common English word list for semantic substitution detection ──────────────
# Words a child might substitute when guessing from context (real words, wrong choice).
_COMMON_WORDS = frozenset([
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "must", "and", "or", "but",
    "not", "in", "on", "at", "to", "for", "of", "by", "with", "about",
    "like", "so", "if", "when", "then", "this", "that", "these", "those",
    "it", "he", "she", "they", "we", "you", "his", "her", "their", "our",
    "its", "my", "your", "big", "small", "little", "said", "went", "came",
    "home", "dog", "cat", "fish", "bird", "run", "jump", "play", "read",
    "book", "went", "look", "see", "saw", "come", "go", "get", "got",
    "make", "made", "take", "took", "day", "night", "time", "way", "man",
    "old", "new", "good", "long", "great", "little", "own", "right", "high",
    "place", "world", "where", "much", "before", "more", "also", "back",
    "after", "off", "right", "never", "how", "just", "know", "take", "into",
    "year", "your", "good", "some", "could", "them", "see", "other", "than",
    "then", "now", "look", "only", "come", "its", "over", "think", "also",
    "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
    "girl", "boy", "mom", "dad", "tree", "flower", "sun", "moon", "star",
    "ball", "house", "school", "food", "water", "fire", "earth", "sky",
    "happy", "sad", "angry", "loud", "soft", "fast", "slow", "warm", "cold",
])


def _clean(word: str) -> str:
    """Normalize to lowercase alphabetic only."""
    return re.sub(r'[^a-z]', '', word.lower())


def _levenshtein(a: str, b: str) -> int:
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


def classify_miscue(spoken_word: str, expected_word: str) -> str:
    """
    Classify a single reading error into one of three miscue types.

    VISUAL   — spoken word is visually similar to expected (shape-based confusion).
    SEMANTIC — spoken word is a real word substitution (context guessing).
    NONSENSE — spoken word is not a recognisable word (phonics breakdown).

    Args:
        spoken_word: What the child actually said.
        expected_word: What the passage word was.

    Returns:
        'VISUAL' | 'SEMANTIC' | 'NONSENSE'
    """
    s = _clean(spoken_word)
    e = _clean(expected_word)

    if not s:
        return 'NONSENSE'

    # Short-circuit: identical after cleaning → not actually an error
    if s == e:
        return 'VISUAL'

    # VISUAL: Levenshtein distance ≤ 2 indicates shape-based confusion
    dist = _levenshtein(s, e)
    if len(s) >= 2 and dist <= 2:
        return 'VISUAL'

    # Shared prefix (≥3 chars) also suggests visual confusion
    if len(s) >= 3 and len(e) >= 3 and s[:3] == e[:3]:
        return 'VISUAL'

    # SEMANTIC: spoken is a real common word substitution
    if s in _COMMON_WORDS:
        return 'SEMANTIC'

    # NONSENSE: unrecognisable / phonics breakdown
    return 'NONSENSE'


def analyze_phoneme_errors(missed_words: list, passage_words: list = None) -> dict:
    """
    Identify which phoneme patterns appear most in the missed/mispronounced words.

    Args:
        missed_words: Words the child skipped or substituted.
        passage_words: Full passage word list (unused currently, reserved for future).

    Returns:
        dict mapping phoneme label → miss count, e.g. {"th": 3, "ing": 1}
    """
    weakness_counts: dict = {}
    for word in missed_words:
        w = _clean(word)
        if not w:
            continue
        for phoneme, pattern in PHONEME_PATTERNS.items():
            if pattern.search(w):
                weakness_counts[phoneme] = weakness_counts.get(phoneme, 0) + 1

    return weakness_counts


def compute_reading_style(miscue_counts: dict) -> str:
    """
    Determine the child's dominant reading strategy from the miscue distribution.

    GUESSR  — semantic errors dominate → child guesses from context/meaning.
    DECODER — nonsense errors dominate → child attempts phonics but gets stuck.

    Returns '' if there are too few errors to classify reliably.
    """
    semantic = miscue_counts.get('semantic', 0)
    nonsense = miscue_counts.get('nonsense', 0)
    total = semantic + nonsense + miscue_counts.get('visual', 0)

    if total < 3:
        return ''  # Insufficient data

    if semantic > nonsense:
        return 'GUESSR'
    if nonsense > semantic:
        return 'DECODER'
    return ''  # Equal — ambiguous


def compute_phoneme_accuracy(passage_words: list, missed_words: list) -> float:
    """
    Estimate phoneme-level match rate.

    Approximation: count how many phoneme clusters appear in passage words,
    subtract clusters found in missed words, express as percentage.

    Args:
        passage_words: All words in the passage.
        missed_words: Words the child did not read correctly.

    Returns:
        float: Phoneme accuracy percentage (0.0–100.0)
    """
    def count_clusters(words: list) -> int:
        total = 0
        for w in words:
            wc = _clean(w)
            for pattern in PHONEME_PATTERNS.values():
                if pattern.search(wc):
                    total += 1
        return max(total, 1)

    passage_total = count_clusters(passage_words)
    missed_total = count_clusters(missed_words)
    accuracy = max(0.0, (passage_total - missed_total) / passage_total * 100)
    return round(min(accuracy, 100.0), 1)


def compute_decoding_latency(word_timestamps: list) -> list:
    """
    Compute inter-word pause durations from Whisper word-level timestamp chunks.

    Only records pauses above 0.3 s to filter out natural breath pauses.
    Decoding struggle threshold from PRD: pause > 1.5 s on ≤3-letter words.

    Args:
        word_timestamps: List of dicts with keys 'text', 'start', 'end' (seconds).

    Returns:
        List of dicts: [{'word': str, 'pause_before': float}] for notable pauses.
    """
    if not word_timestamps or len(word_timestamps) < 2:
        return []

    latency_data = []
    for i in range(1, len(word_timestamps)):
        prev = word_timestamps[i - 1]
        curr = word_timestamps[i]
        try:
            pause = round(float(curr['end'] or 0) - float(prev['end'] or 0)
                          if curr['start'] is None
                          else float(curr['start']) - float(prev['end'] or 0), 2)
        except (TypeError, KeyError):
            continue

        if pause > 0.3:
            latency_data.append({
                'word': curr.get('text', '').strip(),
                'pause_before': pause,
            })

    return latency_data


def detect_decoding_struggles(latency_data: list) -> int:
    """
    Count the number of short words (≤3 letters) with a pause > 1.5 s before them.

    Per PRD §2.2: pause > 1.5 s on ≤3-letter words indicates active phoneme decoding
    rather than sight-word recognition.

    Returns:
        int: number of decoding struggle events in this session.
    """
    return sum(
        1 for item in latency_data
        if item.get('pause_before', 0) > 1.5
        and len(_clean(item.get('word', ''))) <= 3
    )


def merge_phonetic_weaknesses(existing: dict, new_errors: dict) -> dict:
    """
    Merge new phoneme error counts into an existing weakness dict (additive).
    Used to accumulate weaknesses across multiple assessment sessions.

    Args:
        existing: Current child.phonetic_weaknesses dict.
        new_errors: Weaknesses from the latest assessment.

    Returns:
        Updated merged dict.
    """
    merged = dict(existing or {})
    for phoneme, count in (new_errors or {}).items():
        merged[phoneme] = merged.get(phoneme, 0) + count
    return merged

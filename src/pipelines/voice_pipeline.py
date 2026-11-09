"""CPU transcription and conservative, token-window name matching."""
import re
import unicodedata
from functools import lru_cache
from rapidfuzz import fuzz


def normalize(text):
    text = unicodedata.normalize('NFKD', text.casefold())
    return ' '.join(re.findall(r'[^\W_]+', ''.join(c for c in text if not unicodedata.combining(c))))


def match_names(transcript, names, score_cutoff=86):
    """Match full names in token windows; short names require exact tokens.

    A repeated/ambiguous identical name remains a suggestion for teacher review.
    The caller never saves these suggestions automatically.
    """
    words = normalize(transcript).split()
    matched = []
    for name in names:
        target = normalize(name)
        tokens = target.split()
        if not tokens:
            continue
        width = len(tokens)
        windows = [' '.join(words[i:i + width]) for i in range(len(words) - width + 1)]
        if any(window == target or (len(target) >= 5 and fuzz.ratio(target, window) >= score_cutoff)
               for window in windows):
            matched.append(name)
    return matched


@lru_cache(maxsize=1)
def _model():
    from faster_whisper import WhisperModel
    from src.database.config import DATA_DIR
    return WhisperModel('tiny', device='cpu', compute_type='int8',
                        download_root=str(DATA_DIR / 'whisper'), cpu_threads=2, num_workers=1)


def transcribe(path):
    """Errors propagate for actionable UI feedback; silence is never a successful roll call."""
    segments, _ = _model().transcribe(str(path), beam_size=3, language='en',
                                     condition_on_previous_text=False)
    return ' '.join(segment.text.strip() for segment in segments).strip()

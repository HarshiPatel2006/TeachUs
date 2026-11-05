from rapidfuzz import process, fuzz
def match_names(transcript, names, score_cutoff=70):
    words=transcript.lower(); return [n for n in names if process.extractOne(n.lower(),[words],scorer=fuzz.partial_ratio,score_cutoff=score_cutoff)]
def transcribe(path):
    try:
        from faster_whisper import WhisperModel
        return next(WhisperModel('tiny',device='cpu',compute_type='int8').transcribe(path)[0]).text
    except Exception: return ''

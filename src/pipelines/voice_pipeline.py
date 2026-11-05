from rapidfuzz import fuzz
def match_names(transcript,names,score_cutoff=70):
 text=transcript.lower();return [n for n in names if fuzz.partial_ratio(n.lower(),text)>=score_cutoff]
def transcribe(path):
 try:
  from faster_whisper import WhisperModel
  segments,_=WhisperModel('tiny',device='cpu',compute_type='int8').transcribe(path);return ' '.join(s.text for s in segments).strip()
 except Exception:return ''

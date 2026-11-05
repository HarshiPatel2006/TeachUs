import hashlib,urllib.request
import numpy as np
def cosine_similarity(a,b):
 a,b=np.asarray(a,float),np.asarray(b,float);n=np.linalg.norm(a)*np.linalg.norm(b);return float(np.dot(a,b)/n) if n else 0.0
def match_embedding(embedding,candidates,threshold=.55):
 scores=[(cosine_similarity(embedding,v),sid) for sid,v in candidates];return max(scores)[1] if scores and max(scores)[0]>=threshold else None
def match_students(embedding,candidates,threshold=.55):return match_embedding(embedding,candidates,threshold)
def download_model(url,destination,sha256=''):
 destination.parent.mkdir(parents=True,exist_ok=True)
 if not destination.exists():urllib.request.urlretrieve(url,destination)
 if sha256 and hashlib.sha256(destination.read_bytes()).hexdigest().lower()!=sha256.lower():destination.unlink(missing_ok=True);raise ValueError('model checksum mismatch')
 return destination
def detect_and_embed(image,model_dir=None):
 try:
  import cv2
  return [] if image is None else []
 except ImportError:return []

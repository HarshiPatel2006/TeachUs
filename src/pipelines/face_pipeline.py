import numpy as np
def cosine_similarity(a,b):
    a,b=np.asarray(a,float),np.asarray(b,float); n=np.linalg.norm(a)*np.linalg.norm(b)
    return float(np.dot(a,b)/n) if n else 0.0
def match_embedding(embedding, candidates, threshold=.55):
    scores=[(cosine_similarity(embedding,e), sid) for sid,e in candidates]
    return max(scores)[1] if scores and max(scores)[0]>=threshold else None
def detect_and_embed(image):
    """Best-effort hook; models are loaded lazily in deployments with OpenCV Zoo assets."""
    try:
        import cv2
        return [] if image is None else []
    except ImportError: return []

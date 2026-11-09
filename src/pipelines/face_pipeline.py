"""YuNet detection and SFace embeddings, CPU only; no model loads at import."""
from __future__ import annotations

import hashlib
import os
import tempfile
import urllib.request
from functools import lru_cache
from pathlib import Path

import numpy as np

from src.database.config import DATA_DIR

# OpenCV Zoo LFS objects. Pinned content hashes are checked on every first load.
MODELS = {
    'yunet': ('face_detection_yunet/face_detection_yunet_2023mar.onnx',
              '8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4'),
    'sface': ('face_recognition_sface/face_recognition_sface_2021dec.onnx',
              '0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79'),
}
MODEL_BASE = 'https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/'
# Higher than the SFace LFW benchmark threshold (0.363), to reduce classroom false positives.
MATCH_THRESHOLD = 0.50
AMBIGUITY_MARGIN = 0.06


def cosine_similarity(a, b):
    a, b = np.asarray(a, dtype=float).ravel(), np.asarray(b, dtype=float).ravel()
    if a.shape != b.shape or not a.size or not np.isfinite(a).all() or not np.isfinite(b).all():
        return 0.0
    denominator = np.linalg.norm(a) * np.linalg.norm(b)
    return float(np.dot(a, b) / denominator) if denominator else 0.0


def match_embedding(embedding, candidates, threshold=MATCH_THRESHOLD, margin=AMBIGUITY_MARGIN):
    """Candidates are (student_id, embedding); collapse multiple photos per student."""
    scores = {}
    for student_id, vector in candidates:
        scores[student_id] = max(scores.get(student_id, -1), cosine_similarity(embedding, vector))
    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    if not ranked or ranked[0][1] < threshold:
        return None
    if len(ranked) > 1 and ranked[0][1] - ranked[1][1] < margin:
        return None
    return ranked[0][0]


match_students = match_embedding


def download_model(url, destination, sha256):
    """Verify downloads before atomic replacement; interrupted files never become cache hits."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and hashlib.sha256(destination.read_bytes()).hexdigest() == sha256:
        return destination
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=destination.parent, delete=False) as output:
            temporary = Path(output.name)
            with urllib.request.urlopen(url, timeout=90) as response:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
        if hashlib.sha256(temporary.read_bytes()).hexdigest() != sha256:
            raise ValueError('Model checksum mismatch. Please retry the download.')
        os.replace(temporary, destination)
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)
    return destination


@lru_cache(maxsize=2)
def model_paths(model_dir=None):
    folder = Path(model_dir or DATA_DIR / 'models')
    return tuple(str(download_model(MODEL_BASE + relative, folder / Path(relative).name, digest))
                 for relative, digest in MODELS.values())


def decode_image(data):
    import cv2
    if hasattr(data, 'getvalue'):
        data = data.getvalue()
    if len(data) > 10 * 1024 * 1024:
        raise ValueError('Choose an image smaller than 10 MB.')
    image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError('This image could not be read. Try a JPEG or PNG.')
    height, width = image.shape[:2]
    if height * width > 40_000_000:
        raise ValueError('Image is too large. Use a photo below 40 megapixels.')
    if max(height, width) > 2000:
        image = cv2.resize(image, (round(width * 2000 / max(height, width)),
                                   round(height * 2000 / max(height, width))))
    return image


def detect_and_embed(image, model_dir=None):
    """Return face crops and 128-dimensional vectors, ordered left-to-right."""
    import cv2
    if not isinstance(image, np.ndarray):
        image = decode_image(image)
    detector_path, recognizer_path = model_paths(model_dir)
    height, width = image.shape[:2]
    # Instances are local to this request; OpenCV detectors are mutable, not shared across sessions.
    detector = cv2.FaceDetectorYN.create(detector_path, '', (width, height), 0.85, 0.3, 5000)
    recognizer = cv2.FaceRecognizerSF.create(recognizer_path, '')
    _, faces = detector.detect(image)
    results = []
    for face in sorted(faces if faces is not None else [], key=lambda f: f[0]):
        aligned = recognizer.alignCrop(image, face)
        vector = recognizer.feature(aligned).flatten()
        ok, encoded = cv2.imencode('.jpg', aligned)
        if ok:
            results.append({'embedding': vector.tolist(), 'photo': encoded.tobytes(),
                            'box': face[:4].tolist(), 'confidence': float(face[-1])})
    return results


def recognize_photos(uploads, candidates):
    present, detected, unknown = set(), 0, 0
    for upload in uploads:
        for face in detect_and_embed(upload):
            detected += 1
            student_id = match_embedding(face['embedding'], candidates)
            if student_id:
                present.add(student_id)
            else:
                unknown += 1
    return present, detected, unknown

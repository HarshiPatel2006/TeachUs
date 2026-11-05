import hashlib
import numpy as np
import pytest
from src.pipelines.face_pipeline import cosine_similarity, match_embedding, download_model
from src.pipelines.voice_pipeline import match_names, transcribe


def test_face_matching_multiple_embeddings_and_unknowns():
    a, b = np.eye(128)[:2]
    assert cosine_similarity(a, a * 2) == pytest.approx(1)
    assert cosine_similarity(a, b) == 0
    assert cosine_similarity(np.zeros(128), a) == 0
    assert cosine_similarity([float('nan')], [1]) == 0
    assert match_embedding(a, [('one', b), ('one', a), ('two', b)]) == 'one'
    assert match_embedding(a, [('one', b)]) is None
    assert match_embedding(a, []) is None
    assert match_embedding(a, [('one', a), ('two', a)]) is None
    assert match_embedding([.49, (1 - .49**2)**.5], [('one', [1, 0])]) is None


def test_model_checksum_and_failed_download_cleanup(tmp_path):
    source = tmp_path / 'source'
    source.write_bytes(b'model fixture')
    target = tmp_path / 'cache' / 'model'
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    assert download_model(source.as_uri(), target, digest).read_bytes() == b'model fixture'
    target.write_bytes(b'corrupted')
    assert download_model(source.as_uri(), target, digest).read_bytes() == b'model fixture'
    with pytest.raises(ValueError, match='checksum'):
        download_model(source.as_uri(), tmp_path / 'wrong', '0' * 64)
    assert not (tmp_path / 'wrong').exists()
    assert list((tmp_path / 'cache').iterdir()) == [target]


def test_voice_name_matching_is_token_aware():
    names = ['Alice Patel', 'Robert Smith', 'Ann', 'Bob', 'José García', '']
    assert match_names('Alice Patel, Rob ert Smith, José García', names) == ['Alice Patel', 'José García']
    assert match_names('Alyce Patel and Robert Smith are here', names) == ['Alice Patel', 'Robert Smith']
    assert match_names('Joanne and Bobby', names) == []
    assert match_names('Ann, Bob', names) == ['Ann', 'Bob']
    assert match_names('', names) == []


def test_transcription_surfaces_model_errors(monkeypatch):
    import src.pipelines.voice_pipeline as voice
    def fail():
        raise RuntimeError('download unavailable')
    monkeypatch.setattr(voice, '_model', fail)
    with pytest.raises(RuntimeError, match='download unavailable'):
        transcribe('unused.wav')

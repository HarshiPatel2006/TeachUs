from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.database.db import Database


@pytest.fixture
def classroom(tmp_path):
    db = Database(tmp_path / 'test.db')
    teacher = db.create_user('teacher@example.com', 'classroom123', 'Alex Teacher', 'teacher')
    db.actor = teacher
    subject = db.create_subject('Physics')
    yield db, subject
    db.close()

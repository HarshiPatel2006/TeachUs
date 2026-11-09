from datetime import date, timedelta
import sqlite3
import numpy as np
import pytest
from src.database.db import Database


def test_authentication_and_password_hashes(classroom):
    db, subject = classroom
    assert db.user('  TEACHER@example.com ', 'classroom123')['name'] == 'Alex Teacher'
    assert db.user('teacher@example.com', 'wrong') is None
    stored = db.backend.select('users')[0]['password']
    assert 'classroom123' not in stored
    assert Database.verify('classroom123', stored)
    assert Database.hash_password('classroom123') != Database.hash_password('classroom123')
    assert 'password' not in db.user('teacher@example.com', 'classroom123')
    with pytest.raises(ValueError):
        db.create_user('teacher@example.com', 'password123', 'Duplicate')
    with pytest.raises(ValueError):
        db.create_user('bad email', 'password123', 'Invalid')


def test_manual_enrollment_claim_join_and_access(classroom):
    db, subject = classroom
    student = db.enroll(subject['id'], 'Kim Student', 'kim@example.com')
    db.enroll(subject['id'], 'Kim Student', 'kim@example.com')
    assert len(db.students(subject['id'])) == 1
    teacher = db.actor
    user = db.create_user('kim@example.com', 'password123', 'Kim Student')
    db.actor = user
    assert db.own_student()['id'] == student['id']
    assert db.subjects() == [subject]
    db.join(subject['code'].lower())
    with pytest.raises(PermissionError):
        db.create_subject('Not allowed')
    with pytest.raises(PermissionError):
        db.students(subject['id'])
    stranger = db.create_user('stranger@example.com', 'password123', 'Other')
    db.actor = stranger
    with pytest.raises(PermissionError):
        db.attendance(subject['id'])
    with pytest.raises(ValueError):
        db.join('INVALID')
    db.actor = teacher
    assert len(db.students(subject['id'])) == 1


def test_attendance_upsert_filters_privacy_and_csv(classroom):
    db, subject = classroom
    first = db.enroll(subject['id'], '=FORMULA', 'one@example.com')
    second = db.enroll(subject['id'], 'Second Student', 'two@example.com')
    today = date.today()
    yesterday = today - timedelta(days=1)
    records = {first['id']: True, second['id']: False}
    db.take_attendance(subject['id'], records, 'face', yesterday)
    db.take_attendance(subject['id'], records, 'voice', today)
    records[first['id']] = False
    db.take_attendance(subject['id'], records, 'manual', today, [first['id']])
    assert len(db.attendance(subject['id'])) == 4
    rows = db.attendance(subject['id'], today, today)
    assert len(rows) == 2
    assert next(r for r in rows if r['student_id'] == first['id'])['overridden']
    assert "'=FORMULA" in db.attendance_csv(subject['id'])
    with pytest.raises(ValueError):
        db.take_attendance(subject['id'], {first['id']: True}, 'face')
    with pytest.raises(ValueError):
        db.take_attendance(subject['id'], records, 'face', today + timedelta(days=1))
    user = db.create_user('one@example.com', 'password123', 'First')
    db.actor = user
    assert len(db.attendance(subject['id'])) == 2
    assert all(r['student_id'] == first['id'] for r in db.attendance(subject['id']))
    assert 'two@example.com' not in db.attendance_csv(subject['id'])
    with pytest.raises(PermissionError):
        db.take_attendance(subject['id'], records, 'manual')


def test_private_photo_storage_and_persistence(classroom):
    db, subject = classroom
    student = db.enroll(subject['id'], 'Pat', 'pat@example.com')
    vector = np.zeros(128)
    vector[0] = 1
    db.add_photo(student['id'], b'jpeg bytes', vector, subject['id'])
    assert db.embeddings(student['id'], subject['id']) == [vector.tolist()]
    assert len(list(db.files.rglob('*.jpg'))) == 1
    with pytest.raises(ValueError):
        db.add_photo(student['id'], b'x', [0, 1], subject['id'])
    teacher = db.actor
    other = db.create_user('other@example.com', 'password123', 'Other Teacher', 'teacher')
    db.actor = other
    with pytest.raises(PermissionError):
        db.embeddings(student['id'], subject['id'])
    with pytest.raises(PermissionError):
        db.add_photo(student['id'], b'x', vector, subject['id'])
    path = db.backend.conn.execute('PRAGMA database_list').fetchone()[2]
    db.close()
    reopened = Database(path, actor=teacher)
    assert len(reopened.students(subject['id'])) == 1
    assert len(reopened.embeddings(student['id'], subject['id'])) == 1
    reopened.close()


def test_sqlite_enforces_foreign_keys(classroom):
    db, subject = classroom
    with pytest.raises(sqlite3.IntegrityError):
        db.backend.insert('enrollments', {'id': 'x', 'subject_id': subject['id'],
                                         'student_id': 'nonexistent', 'created_at': '2026-01-01'})


def test_dialog_can_resume_after_full_page_closes_connection(classroom):
    db, subject = classroom
    db.close()
    student = db.enroll(subject['id'], 'Dialog Student', 'dialog@example.com')
    assert db.students(subject['id'])[0]['id'] == student['id']

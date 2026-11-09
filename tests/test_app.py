from pathlib import Path
from streamlit.testing.v1 import AppTest
from src.database.db import Database

APP = Path(__file__).resolve().parents[1] / 'app.py'


def test_home_screen_smoke(tmp_path, monkeypatch):
    import src.database.db as db_module
    monkeypatch.setattr(db_module, 'get_db', lambda actor=None: Database(tmp_path / 'app.db', actor))
    at = AppTest.from_file(str(APP), default_timeout=20).run()
    assert not at.exception
    assert not at.error
    assert any('Create account' == tab.label for tab in at.tabs)
    assert at.radio[0].options == ['Teacher', 'Student']
    assert any('TeachUs' in item.value for item in at.markdown)


def test_teacher_and_student_workspaces(tmp_path, monkeypatch):
    import src.database.db as db_module
    path = tmp_path / 'app.db'
    db = Database(path)
    teacher = db.create_user('teacher@example.com', 'password123', 'Teacher Name', 'teacher')
    db.actor = teacher
    subject = db.create_subject('Mathematics')
    student = db.create_user('student@example.com', 'password123', 'Student Name')
    db.actor = student
    db.join(subject['code'])
    db.close()
    monkeypatch.setattr(db_module, 'get_db', lambda actor=None: Database(path, actor))
    for user in (teacher, student):
        at = AppTest.from_file(str(APP), default_timeout=20)
        at.session_state['user'] = user
        at.run()
        assert not at.exception
        assert not at.error
        next(button for button in at.button if button.label == 'Open subject →').click().run()
        assert not at.exception
        assert not at.error
        if user['role'] == 'teacher':
            assert any(tab.label == 'Class roster' for tab in at.tabs)
            next(button for button in at.button if button.label == 'Enrol from group photo').click().run()
            assert not at.exception
        else:
            assert any('not saved any attendance' in item.value for item in at.info)


def test_dialog_forms_create_enroll_and_save(tmp_path):
    # AppTest runs whole scripts, not fragment-only events. Keep each dialog
    # mounted in a small harness, matching the browser's fragment lifecycle.
    path = tmp_path / 'dialogs.db'
    db = Database(path)
    teacher = db.create_user('teacher@example.com', 'password123', 'Teacher Name', 'teacher')
    db.close()
    prefix = f"""
import streamlit as st
from src.database.db import Database
from src.components.dialog_create_subject import dialog_create_subject
from src.components.dialog_enroll import dialog_enroll
from src.components.dialog_attendance_results import dialog_attendance_results, queue_results
db = Database({str(path)!r}, {teacher!r})
"""
    at = AppTest.from_string(prefix + """
if not db.subjects():
    dialog_create_subject(db)
else:
    st.title(db.subjects()[0]['name'])
""", default_timeout=20).run()
    at.text_input[0].input('Biology')
    next(b for b in at.button if b.label == 'Create subject').click().run()
    assert not at.exception
    assert not at.error
    assert at.title[0].value == 'Biology'
    at = AppTest.from_string(prefix + """
subject = db.subjects()[0]
if not db.students(subject['id']):
    dialog_enroll(db, subject)
else:
    st.write('Enrolled')
""", default_timeout=20).run()
    next(w for w in at.text_input if w.label == 'Full name').input('Maya Student')
    next(w for w in at.text_input if w.label == 'Student email').input('maya@example.com')
    next(b for b in at.button if b.label == 'Enrol student').click().run()
    assert not at.exception
    assert not at.error
    at = AppTest.from_string(prefix + """
subject = db.subjects()[0]
if not db.attendance(subject['id']):
    if 'attendance_review' not in st.session_state:
        queue_results(subject['id'], db.students(subject['id']), set(), 'manual')
    dialog_attendance_results(db, st.session_state['attendance_review'])
else:
    st.write('Saved')
""", default_timeout=20).run()
    next(w for w in at.checkbox if 'reviewed this attendance' in w.label).check().run()
    next(b for b in at.button if b.label == 'Save attendance').click().run()
    assert not at.exception
    assert not at.error
    check = Database(path, teacher)
    rows = check.attendance(check.subjects()[0]['id'])
    assert len(rows) == 1
    assert rows[0]['name'] == 'Maya Student'
    assert rows[0]['source'] == 'manual'
    check.close()


def test_signup_and_signout(tmp_path, monkeypatch):
    import src.database.db as db_module
    path = tmp_path / 'auth.db'
    monkeypatch.setattr(db_module, 'get_db', lambda actor=None: Database(path, actor))
    at = AppTest.from_file(str(APP), default_timeout=20).run()
    at.text_input(key='signup_name').input('Taylor Teacher')
    at.text_input(key='signup_email').input('taylor@example.com')
    at.text_input(key='signup_password').input('password123')
    next(w for w in at.text_input if w.label == 'Confirm password').input('password123')
    next(b for b in at.button if b.label == 'Create teacher account').click().run()
    assert not at.exception
    assert not at.error
    assert any('Hello, Taylor' in title.value for title in at.title)
    next(b for b in at.button if b.label == 'Sign out').click().run()
    assert not at.exception
    assert not at.error
    assert at.radio[0].options == ['Teacher', 'Student']

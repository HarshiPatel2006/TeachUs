"""One authorized application interface over SQLite or server-side Supabase.

Supabase uses a service role key: browsers never receive the client or credentials.
All domain methods enforce the signed-in actor, including roster and photo access.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import secrets
import sqlite3
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

from .config import BUCKET, DATA_DIR, DB_PATH, credentials, use_supabase

SCHEMA = '''
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS users (
 id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, password TEXT NOT NULL,
 name TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('student','teacher')),
 created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS subjects (
 id TEXT PRIMARY KEY, owner_id TEXT NOT NULL REFERENCES users(id),
 name TEXT NOT NULL, code TEXT UNIQUE NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS students (
 id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
 user_id TEXT UNIQUE REFERENCES users(id), created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS enrollments (
 id TEXT PRIMARY KEY, subject_id TEXT NOT NULL REFERENCES subjects(id),
 student_id TEXT NOT NULL REFERENCES students(id), created_at TEXT NOT NULL,
 UNIQUE(subject_id,student_id));
CREATE TABLE IF NOT EXISTS photos (
 id TEXT PRIMARY KEY, student_id TEXT NOT NULL REFERENCES students(id),
 path TEXT NOT NULL, embedding TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS attendance (
 id TEXT PRIMARY KEY, subject_id TEXT NOT NULL REFERENCES subjects(id),
 student_id TEXT NOT NULL REFERENCES students(id), date TEXT NOT NULL,
 present INTEGER NOT NULL, source TEXT NOT NULL, overridden INTEGER NOT NULL,
 created_at TEXT NOT NULL, UNIQUE(subject_id,student_id,date));
CREATE INDEX IF NOT EXISTS attendance_subject_date ON attendance(subject_id,date);
CREATE INDEX IF NOT EXISTS enrollment_student ON enrollments(student_id);
CREATE INDEX IF NOT EXISTS photo_student ON photos(student_id);
'''
TABLES = {'users', 'subjects', 'students', 'enrollments', 'photos', 'attendance'}


def now():
    return datetime.now(timezone.utc).isoformat()


class SQLiteBackend:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self._conn = None
        self.conn.executescript(SCHEMA)

    @property
    def conn(self):
        # Dialog fragments can outlive the full-page run that created this backend.
        if self._conn is None:
            self._conn = sqlite3.connect(self.path, timeout=20, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute('PRAGMA foreign_keys=ON')
        return self._conn

    def select(self, table, **filters):
        assert table in TABLES
        where = ' AND '.join(f'{key}=?' for key in filters)
        return [dict(row) for row in self.conn.execute(
            f'SELECT * FROM {table}' + (' WHERE ' + where if where else ''),
            tuple(filters.values()))]

    def insert(self, table, row):
        assert table in TABLES
        self.conn.execute(f'INSERT INTO {table} ({",".join(row)}) VALUES '
                          f'({",".join("?" for _ in row)})', tuple(row.values()))
        self.conn.commit()

    def upsert_attendance(self, rows):
        with self.conn:
            for row in rows:
                self.conn.execute(
                    f'INSERT INTO attendance ({",".join(row)}) VALUES '
                    f'({",".join("?" for _ in row)}) ON CONFLICT(subject_id,student_id,date) '
                    'DO UPDATE SET present=excluded.present,source=excluded.source,'
                    'overridden=excluded.overridden,created_at=excluded.created_at',
                    tuple(row.values()))

    def close(self):
        if self._conn is not None:
            self._conn.close()
            self._conn = None


class SupabaseBackend:
    def __init__(self):
        from supabase import create_client
        self.client = create_client(*credentials())

    def select(self, table, **filters):
        query = self.client.table(table).select('*')
        for key, value in filters.items():
            query = query.eq(key, value)
        return query.execute().data

    def insert(self, table, row):
        self.client.table(table).insert(row).execute()

    def upsert_attendance(self, rows):
        # Single PostgREST request is a database transaction.
        self.client.table('attendance').upsert(
            rows, on_conflict='subject_id,student_id,date').execute()

    def close(self):
        pass


class Database:
    def __init__(self, path=None, actor=None, backend=None):
        self.backend = backend or (SQLiteBackend(path) if path is not None else
                                  SupabaseBackend() if use_supabase() else SQLiteBackend(DB_PATH))
        self.actor = actor
        self.files = Path(path).parent / 'photos' if path else DATA_DIR / 'photos'

    def _all(self, table, **filters):
        return self.backend.select(table, **filters)

    def _one(self, table, **filters):
        rows = self._all(table, **filters)
        return rows[0] if rows else None

    def _insert(self, table, **fields):
        row = dict(id=str(uuid.uuid4()), **fields, created_at=now())
        self.backend.insert(table, row)
        return row

    def _require(self, role=None):
        if not self.actor or (role and self.actor['role'] != role):
            raise PermissionError('Please sign in with the appropriate account.')

    @staticmethod
    def hash_password(password, salt=None):
        salt = salt or secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 600_000)
        return salt + '$' + digest.hex()

    @staticmethod
    def verify(password, stored):
        try:
            return secrets.compare_digest(Database.hash_password(password, stored.split('$')[0]), stored)
        except (ValueError, AttributeError):
            return False

    @staticmethod
    def _email(email):
        email = email.strip().lower()
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
            raise ValueError('Enter a valid email address.')
        return email

    def create_user(self, email, password, name, role='student'):
        email = self._email(email)
        if not name.strip() or len(name) > 100 or len(password) < 8 or role not in ('teacher', 'student'):
            raise ValueError('Provide a name and a password of at least 8 characters.')
        if self._one('users', email=email):
            raise ValueError('This email is already registered. Please sign in.')
        row = self._insert('users', email=email, password=self.hash_password(password),
                           name=name.strip(), role=role)
        return {k: v for k, v in row.items() if k != 'password'}

    def user(self, email, password):
        row = self._one('users', email=email.strip().lower())
        if row and self.verify(password, row['password']):
            return {k: v for k, v in row.items() if k != 'password'}
        return None

    def _profile(self):
        self._require('student')
        row = self._one('students', email=self.actor['email'])
        return row or self._insert('students', email=self.actor['email'],
                                   name=self.actor['name'], user_id=self.actor['id'])

    def subject(self, subject_id):
        self._require()
        row = self._one('subjects', id=subject_id)
        if not row:
            raise ValueError('Subject no longer exists.')
        if row['owner_id'] == self.actor['id']:
            return row
        if self.actor['role'] == 'student' and self._one(
                'enrollments', subject_id=subject_id, student_id=self._profile()['id']):
            return row
        raise PermissionError('You do not have access to this subject.')

    def _owner(self, subject_id):
        self._require('teacher')
        subject = self.subject(subject_id)
        if subject['owner_id'] != self.actor['id']:
            raise PermissionError('Only the subject teacher can do this.')
        return subject

    def create_subject(self, name):
        self._require('teacher')
        if not name.strip() or len(name) > 120:
            raise ValueError('Use a subject name of 1–120 characters.')
        code = ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(8))
        return self._insert('subjects', owner_id=self.actor['id'], name=name.strip(), code=code)

    def subjects(self):
        self._require()
        if self.actor['role'] == 'teacher':
            rows = self._all('subjects', owner_id=self.actor['id'])
        else:
            rows = [self._one('subjects', id=e['subject_id']) for e in
                    self._all('enrollments', student_id=self._profile()['id'])]
        return sorted(rows, key=lambda s: s['name'].casefold())

    def _enroll(self, subject_id, student):
        if not self._one('enrollments', subject_id=subject_id, student_id=student['id']):
            self._insert('enrollments', subject_id=subject_id, student_id=student['id'])
        return student

    def join(self, code):
        self._require('student')
        subject = self._one('subjects', code=code.strip().upper())
        if not subject:
            raise ValueError('No subject found. Check the join code with your teacher.')
        self._enroll(subject['id'], self._profile())
        return subject

    def enroll(self, subject_id, name, email):
        self._owner(subject_id)
        email = self._email(email)
        if not name.strip() or len(name) > 100:
            raise ValueError('Provide a student name of 1–100 characters.')
        user = self._one('users', email=email)
        if user and user['role'] != 'student':
            raise ValueError('That email belongs to a teacher account.')
        student = self._one('students', email=email) or self._insert(
            'students', name=name.strip(), email=email, user_id=user['id'] if user else None)
        return self._enroll(subject_id, student)

    def students(self, subject_id):
        self._owner(subject_id)
        return sorted([self._one('students', id=e['student_id']) for e in
                       self._all('enrollments', subject_id=subject_id)], key=lambda s: s['name'])

    def own_student(self):
        return self._profile()

    def _photo_access(self, student_id, subject_id=None):
        self._require()
        if self.actor['role'] == 'student' and self._profile()['id'] == student_id:
            return
        if subject_id:
            self._owner(subject_id)
            if self._one('enrollments', subject_id=subject_id, student_id=student_id):
                return
        raise PermissionError('You do not have access to these face photos.')

    def add_photo(self, student_id, image_bytes, embedding, subject_id=None):
        self._photo_access(student_id, subject_id)
        import numpy as np
        vector = np.asarray(embedding, dtype=float).flatten()
        if vector.size != 128 or not np.isfinite(vector).all() or not np.linalg.norm(vector):
            raise ValueError('Invalid SFace embedding.')
        if len(image_bytes) > 10 * 1024 * 1024:
            raise ValueError('Photo must be smaller than 10 MB.')
        key = f'{student_id}/{uuid.uuid4()}.jpg'
        if isinstance(self.backend, SupabaseBackend):
            self.backend.client.storage.from_(BUCKET).upload(
                key, image_bytes, {'content-type': 'image/jpeg'})
        else:
            target = self.files / key
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(image_bytes)
        try:
            self._insert('photos', student_id=student_id, path=key, embedding=json.dumps(vector.tolist()))
        except Exception:
            if isinstance(self.backend, SupabaseBackend):
                self.backend.client.storage.from_(BUCKET).remove([key])
            else:
                (self.files / key).unlink(missing_ok=True)
            raise

    def embeddings(self, student_id, subject_id=None):
        self._photo_access(student_id, subject_id)
        return [json.loads(p['embedding']) for p in self._all('photos', student_id=student_id)]

    def take_attendance(self, subject_id, records, source, taken_on=None, overrides=()):
        self._owner(subject_id)
        day = date.fromisoformat(str(taken_on or date.today())).isoformat()
        if day > date.today().isoformat():
            raise ValueError('Attendance cannot be saved in the future.')
        roster = {s['id'] for s in self.students(subject_id)}
        if not roster or set(records) != roster or source not in ('face', 'voice', 'manual'):
            raise ValueError('Review the complete current roster before saving attendance.')
        rows = [dict(id=str(uuid.uuid4()), subject_id=subject_id, student_id=sid,
                     date=day, present=bool(present), source=source,
                     overridden=sid in overrides, created_at=now()) for sid, present in records.items()]
        self.backend.upsert_attendance(rows)

    def attendance(self, subject_id, start=None, end=None):
        self.subject(subject_id)
        filters = {'subject_id': subject_id}
        if self.actor['role'] == 'student':
            filters['student_id'] = self._profile()['id']
        rows = self._all('attendance', **filters)
        rows = [r for r in rows if (not start or r['date'] >= str(start))
                and (not end or r['date'] <= str(end))]
        for row in rows:
            student = self._one('students', id=row['student_id'])
            row.update(name=student['name'], email=student['email'])
        return sorted(rows, key=lambda r: (r['date'], r['name']), reverse=True)

    def attendance_csv(self, subject_id, start=None, end=None):
        output = io.StringIO()
        fields = ['date', 'name', 'email', 'present', 'source', 'overridden']
        writer = csv.DictWriter(output, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        for row in self.attendance(subject_id, start, end):
            # Prevent spreadsheet formula injection from user-supplied names.
            writer.writerow({k: "'" + v if isinstance(v, str) and v.startswith(('=', '+', '-', '@'))
                             else v for k, v in row.items() if k in fields})
        return output.getvalue()

    def close(self):
        self.backend.close()


def get_db(actor=None):
    return Database(actor=actor)

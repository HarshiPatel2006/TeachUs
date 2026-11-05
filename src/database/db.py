"""Persistence interface. SQLite is the zero-configuration backend."""
import hashlib, os, secrets, sqlite3
from datetime import datetime
from pathlib import Path
from .config import DB_PATH, DATA_DIR, use_supabase

class Database:
    def __init__(self, path=DB_PATH):
        self.path = Path(path); self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row; self._init()
    def _init(self):
        self.conn.executescript('''CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,email TEXT UNIQUE NOT NULL,password TEXT NOT NULL,name TEXT DEFAULT '',role TEXT NOT NULL); CREATE TABLE IF NOT EXISTS subjects(id INTEGER PRIMARY KEY,owner_id INTEGER,name TEXT NOT NULL,code TEXT UNIQUE NOT NULL,created_at TEXT NOT NULL); CREATE TABLE IF NOT EXISTS enrollments(subject_id INTEGER,student_id INTEGER,joined_at TEXT NOT NULL,PRIMARY KEY(subject_id,student_id)); CREATE TABLE IF NOT EXISTS photos(id INTEGER PRIMARY KEY,student_id INTEGER,path TEXT,embedding TEXT); CREATE TABLE IF NOT EXISTS attendance(id INTEGER PRIMARY KEY,subject_id INTEGER,student_id INTEGER,date TEXT NOT NULL,present INTEGER DEFAULT 0,source TEXT DEFAULT 'face',UNIQUE(subject_id,student_id,date));'''); self.conn.commit()
    @staticmethod
    def hash_password(password, salt=None):
        salt = salt or secrets.token_hex(16); return salt+'$'+hashlib.pbkdf2_hmac('sha256',password.encode(),salt.encode(),160000).hex()
    @staticmethod
    def verify(password, stored):
        try: salt, digest=stored.split('$',1); return secrets.compare_digest(Database.hash_password(password,salt),stored)
        except ValueError: return False
    def create_user(self,email,password,name='',role='student'):
        try:
            cur=self.conn.execute('INSERT INTO users(email,password,name,role) VALUES(?,?,?,?)',(email.lower().strip(),self.hash_password(password),name,role)); self.conn.commit(); return cur.lastrowid
        except sqlite3.IntegrityError: return None
    def user(self,email,password):
        r=self.conn.execute('SELECT * FROM users WHERE email=?',(email.lower().strip(),)).fetchone(); return dict(r) if r and self.verify(password,r['password']) else None
    def subjects(self, owner_id=None, student_id=None):
        if owner_id is not None: q='SELECT * FROM subjects WHERE owner_id=? ORDER BY id DESC'; args=(owner_id,)
        else: q='SELECT s.* FROM subjects s JOIN enrollments e ON e.subject_id=s.id WHERE e.student_id=?'; args=(student_id,)
        return [dict(r) for r in self.conn.execute(q,args)]
    def create_subject(self,owner_id,name):
        import string
        while True:
            code=''.join(secrets.choice(string.ascii_uppercase+string.digits) for _ in range(6))
            try: cur=self.conn.execute('INSERT INTO subjects(owner_id,name,code,created_at) VALUES(?,?,?,?)',(owner_id,name,code,datetime.now().isoformat())); self.conn.commit(); return dict(self.conn.execute('SELECT * FROM subjects WHERE id=?',(cur.lastrowid,)).fetchone())
            except sqlite3.IntegrityError: pass
    def join(self,student_id,code):
        s=self.conn.execute('SELECT * FROM subjects WHERE code=?',(code.upper().strip(),)).fetchone()
        if not s:return False
        self.conn.execute('INSERT OR IGNORE INTO enrollments VALUES(?,?,?)',(s['id'],student_id,datetime.now().isoformat())); self.conn.commit(); return True
    def mark(self,subject_id,student_id,present,date=None,source='face'):
        date=date or datetime.now().date().isoformat(); self.conn.execute('INSERT INTO attendance(subject_id,student_id,date,present,source) VALUES(?,?,?,?,?) ON CONFLICT(subject_id,student_id,date) DO UPDATE SET present=excluded.present,source=excluded.source',(subject_id,student_id,date,int(present),source)); self.conn.commit()
    def attendance(self,subject_id): return [dict(r) for r in self.conn.execute('SELECT a.*,u.name,u.email FROM attendance a JOIN users u ON u.id=a.student_id WHERE subject_id=? ORDER BY date DESC',(subject_id,))]

def get_db(): return Database()

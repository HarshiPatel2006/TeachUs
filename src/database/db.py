"""Persistence interface with SQLite and optional Supabase."""
from __future__ import annotations
import csv,hashlib,io,json,secrets,sqlite3
from datetime import date,datetime
from pathlib import Path
from .config import DB_PATH,use_supabase
SCHEMA='''CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,email TEXT UNIQUE NOT NULL,password TEXT NOT NULL,name TEXT NOT NULL,role TEXT NOT NULL,created_at TEXT NOT NULL);CREATE TABLE IF NOT EXISTS subjects(id INTEGER PRIMARY KEY,owner_id INTEGER NOT NULL,name TEXT NOT NULL,code TEXT UNIQUE NOT NULL,created_at TEXT NOT NULL);CREATE TABLE IF NOT EXISTS enrollments(subject_id INTEGER,student_id INTEGER,joined_at TEXT NOT NULL,PRIMARY KEY(subject_id,student_id));CREATE TABLE IF NOT EXISTS photos(id INTEGER PRIMARY KEY,student_id INTEGER,path TEXT,embedding TEXT,created_at TEXT NOT NULL);CREATE TABLE IF NOT EXISTS attendance_sessions(id INTEGER PRIMARY KEY,subject_id INTEGER,taken_on TEXT NOT NULL,source TEXT NOT NULL);CREATE TABLE IF NOT EXISTS attendance(id INTEGER PRIMARY KEY,session_id INTEGER,subject_id INTEGER,student_id INTEGER,date TEXT NOT NULL,present INTEGER DEFAULT 0,source TEXT NOT NULL,overridden INTEGER DEFAULT 0,UNIQUE(subject_id,student_id,date));CREATE INDEX IF NOT EXISTS attendance_subject_date ON attendance(subject_id,date);'''
class Database:
 def __init__(self,path=DB_PATH):
  self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True);self.conn=sqlite3.connect(self.path,check_same_thread=False);self.conn.row_factory=sqlite3.Row;self.conn.executescript(SCHEMA);self.conn.commit()
 @staticmethod
 def hash_password(password,salt=None):
  salt=salt or secrets.token_hex(16);return salt+'$'+hashlib.pbkdf2_hmac('sha256',password.encode(),salt.encode(),210000).hex()
 @staticmethod
 def verify(password,stored):
  try:return secrets.compare_digest(Database.hash_password(password,stored.split('$',1)[0]),stored)
  except (ValueError,AttributeError):return False
 def create_user(self,email,password,name='',role='student'):
  try:c=self.conn.execute('INSERT INTO users(email,password,name,role,created_at) VALUES(?,?,?,?,?)',(email.strip().lower(),self.hash_password(password),name.strip(),role,datetime.utcnow().isoformat()));self.conn.commit();return c.lastrowid
  except sqlite3.IntegrityError:return None
 def user(self,email,password):
  r=self.conn.execute('SELECT * FROM users WHERE email=?',(email.strip().lower(),)).fetchone();return dict(r) if r and self.verify(password,r['password']) else None
 def create_subject(self,owner_id,name):
  while True:
   code=''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(6))
   try:c=self.conn.execute('INSERT INTO subjects(owner_id,name,code,created_at) VALUES(?,?,?,?)',(owner_id,name.strip(),code,datetime.utcnow().isoformat()));self.conn.commit();return self.subject(c.lastrowid)
   except sqlite3.IntegrityError:continue
 def subject(self,subject_id):
  r=self.conn.execute('SELECT * FROM subjects WHERE id=?',(subject_id,)).fetchone();return dict(r) if r else None
 def subjects(self,owner_id=None,student_id=None):
  q,a=('SELECT * FROM subjects WHERE owner_id=? ORDER BY id DESC',(owner_id,)) if owner_id is not None else ('SELECT s.* FROM subjects s JOIN enrollments e ON e.subject_id=s.id WHERE e.student_id=? ORDER BY s.name',(student_id,));return [dict(r) for r in self.conn.execute(q,a)]
 def enroll(self,student_id,subject_id):self.conn.execute('INSERT OR IGNORE INTO enrollments VALUES(?,?,?)',(subject_id,student_id,datetime.utcnow().isoformat()));self.conn.commit();return True
 def join(self,student_id,code):
  r=self.conn.execute('SELECT id FROM subjects WHERE code=?',(code.strip().upper(),)).fetchone();return bool(r and self.enroll(student_id,r['id']))
 def students(self,subject_id):return [dict(r) for r in self.conn.execute('SELECT u.* FROM users u JOIN enrollments e ON e.student_id=u.id WHERE e.subject_id=? ORDER BY u.name',(subject_id,))]
 def add_photo(self,student_id,path=None,embedding=None):self.conn.execute('INSERT INTO photos(student_id,path,embedding,created_at) VALUES(?,?,?,?)',(student_id,path,json.dumps(embedding) if embedding is not None else None,datetime.utcnow().isoformat()));self.conn.commit()
 def embeddings(self,student_id):return [json.loads(r['embedding']) for r in self.conn.execute('SELECT embedding FROM photos WHERE student_id=? AND embedding IS NOT NULL',(student_id,))]
 def take_attendance(self,subject_id,records,source='face',taken_on=None,overrides=None):
  d=taken_on or date.today().isoformat();sid=self.conn.execute('INSERT INTO attendance_sessions(subject_id,taken_on,source) VALUES(?,?,?)',(subject_id,d,source)).lastrowid
  for uid,present in records.items():self.conn.execute('INSERT INTO attendance(session_id,subject_id,student_id,date,present,source,overridden) VALUES(?,?,?,?,?,?,?) ON CONFLICT(subject_id,student_id,date) DO UPDATE SET present=excluded.present,source=excluded.source,overridden=excluded.overridden,session_id=excluded.session_id',(sid,subject_id,uid,d,int(bool(present)),source,int(uid in (overrides or set()))))
  self.conn.commit();return sid
 def attendance(self,subject_id,start=None,end=None):
  q='SELECT a.*,u.name,u.email FROM attendance a JOIN users u ON u.id=a.student_id WHERE a.subject_id=?';args=[subject_id]
  if start:q+=' AND date>=?';args.append(start)
  if end:q+=' AND date<=?';args.append(end)
  return [dict(r) for r in self.conn.execute(q+' ORDER BY date DESC,u.name',args)]
 def attendance_csv(self,subject_id,start=None,end=None):
  out=io.StringIO();w=csv.DictWriter(out,fieldnames=['date','name','email','present','source','overridden']);w.writeheader();w.writerows({k:r.get(k) for k in w.fieldnames} for r in self.attendance(subject_id,start,end));return out.getvalue()
 def close(self):self.conn.close()
def get_db():return Database()

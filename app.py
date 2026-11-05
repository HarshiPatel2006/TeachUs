import streamlit as st
from src.database.db import get_db
from src.ui.base_layout import setup,header,footer
from src.components.subject import subject_card
setup();header();db=get_db();st.session_state.setdefault('user',None)
def auth():
 st.title('Welcome to TeachUs');a,b=st.tabs(['Sign in','Create account'])
 with a:
  e=st.text_input('Email',key='login_email');p=st.text_input('Password',type='password',key='login_password')
  if st.button('Sign in',type='primary'):
   u=db.user(e,p)
   if u:st.session_state.user=u;st.rerun()
   else:st.error('Invalid email or password')
 with b:
  n=st.text_input('Full name',key='signup_name');e=st.text_input('Email',key='signup_email');p=st.text_input('Password (8+ characters)',type='password',key='signup_password');r=st.radio('Account type',['student','teacher'],horizontal=True)
  if st.button('Create account',type='primary'):
   if len(p)<8:st.error('Use at least 8 characters.')
   elif db.create_user(e,p,n,r):st.success('Account created. Sign in above.')
   else:st.error('That email is already registered.')
def teacher(u):
 st.title('Teacher dashboard')
 with st.expander('Create a subject',expanded=not db.subjects(owner_id=u['id'])):
  n=st.text_input('Subject name',key='new_subject')
  if st.button('Create subject') and n.strip():db.create_subject(u['id'],n);st.success('Subject created');st.rerun()
 for s in db.subjects(owner_id=u['id']):
  subject_card(s,len(db.students(s['id'])));st.caption(f"Share join code **{s['code']}** with students");st.file_uploader('Class photo',type=['jpg','jpeg','png'],key=f"photo{s['id']}");st.audio_input('Voice roll call',key=f"voice{s['id']}")
  if st.button('View attendance',key=f"view{s['id']}"):
   st.dataframe(db.attendance(s['id']),use_container_width=True);st.download_button('Export CSV',db.attendance_csv(s['id']),'attendance.csv','text/csv')
def student(u):
 st.title('Student dashboard');code=st.text_input('Subject join code').upper()
 if st.button('Join subject'):
  if db.join(u['id'],code):st.success('Joined subject!');st.rerun()
  else:st.error('No subject found for that code.')
 for s in db.subjects(student_id=u['id']):
  subject_card(s);rows=[r for r in db.attendance(s['id']) if r['student_id']==u['id']];pct=sum(r['present'] for r in rows)/len(rows)*100 if rows else 0;st.metric('Attendance',f'{pct:.0f}%');st.dataframe(rows,use_container_width=True)
if not st.session_state.user:auth()
else:
 u=st.session_state.user
 with st.sidebar:
  st.write(f"Signed in as **{u['name']}**")
  if st.button('Sign out'):st.session_state.clear();st.rerun()
 teacher(u) if u['role']=='teacher' else student(u)
footer()

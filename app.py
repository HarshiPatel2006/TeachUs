import streamlit as st
from src.database.db import get_db
from src.ui.base_layout import setup,header,footer
setup(); header(); db=get_db()
if 'user' not in st.session_state: st.session_state.user=None
if not st.session_state.user:
 a,b=st.tabs(['Sign in','Create account'])
 with a:
  email=st.text_input('Email'); pw=st.text_input('Password',type='password')
  if st.button('Sign in',type='primary'):
   u=db.user(email,pw)
   if u: st.session_state.user=u; st.rerun()
   else: st.error('Invalid email or password')
 with b:
  name=st.text_input('Name'); email=st.text_input('Email',key='e'); pw=st.text_input('Password',type='password',key='p'); role=st.radio('I am a',['student','teacher'],horizontal=True)
  if st.button('Create account',type='primary'):
   if len(pw)<8: st.error('Use at least 8 characters')
   elif db.create_user(email,pw,name,role): st.success('Account created—sign in above')
   else: st.error('That email is already registered')
else:
 u=st.session_state.user
 if st.sidebar.button('Sign out'): st.session_state.clear(); st.rerun()
 if u['role']=='teacher':
  st.header('Teacher dashboard'); name=st.text_input('New subject name')
  if st.button('Create subject') and name.strip(): st.success(f"Created: {db.create_subject(u['id'],name)['code']}")
  for s in db.subjects(owner_id=u['id']):
   with st.container(border=True): st.subheader(s['name']); st.code(s['code']); st.caption('Share this code with students'); st.file_uploader('Class photo',type=['jpg','jpeg','png'],key=f"p{s['id']}"); st.audio_input('Voice roll call',key=f"a{s['id']}")
 else:
  st.header('Student dashboard'); code=st.text_input('Subject join code').upper()
  if st.button('Join subject'): st.success('Joined subject') if db.join(u['id'],code) else st.error('Code not found')
  for s in db.subjects(student_id=u['id']): st.subheader(s['name'])
footer()

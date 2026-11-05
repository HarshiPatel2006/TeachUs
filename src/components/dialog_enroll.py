import streamlit as st
@st.dialog('Enroll student')
def enroll_dialog(db,subject_id):
 email=st.text_input('Student email')
 if st.button('Enroll'):
  u=db._one('users',email=email) if hasattr(db,'_one') else None
  if u:db.enroll(u['id'],subject_id);st.success('Enrolled')

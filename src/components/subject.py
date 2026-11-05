import streamlit as st
def subject_card(subject,student_count=None):
 with st.container(border=True):
  st.subheader(subject['name']);st.code(subject['code'])
  if student_count is not None:st.caption(f'{student_count} students')

import streamlit as st
@st.dialog('Auto-enroll from group photo')
def auto_enroll_dialog():
 st.file_uploader('Group photo',type=['jpg','jpeg','png']);st.info('Faces are matched against students with saved photos.')

import streamlit as st
@st.dialog('Share subject')
def share_subject_dialog(subject):
 st.write('Join code');st.code(subject['code']);st.text_input('Copyable link',value=f"TeachUs join code: {subject['code']}",disabled=True)

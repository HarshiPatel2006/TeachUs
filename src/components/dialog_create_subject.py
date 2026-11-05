import streamlit as st
@st.dialog('Create subject')
def create_subject_dialog(db,owner_id):
 name=st.text_input('Subject name')
 if st.button('Create',type='primary') and name.strip(): db.create_subject(owner_id,name);st.rerun()

import streamlit as st
from src.ui.base_layout import notify, show_error


@st.dialog('Create a subject')
def dialog_create_subject(db):
    st.write('Give your class a home. A unique join code is created automatically.')
    with st.form('create_subject'):
        name = st.text_input('Subject name', placeholder='e.g. Introduction to Physics', max_chars=120)
        save = st.form_submit_button('Create subject', type='primary', width='stretch')
    if save:
        try:
            subject = db.create_subject(name)
            st.session_state['subject_id'] = subject['id']
            notify('Subject created. Share the join code to invite students.')
            st.rerun()
        except Exception as error:
            show_error(error)

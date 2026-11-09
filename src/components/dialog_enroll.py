import streamlit as st
from src.ui.base_layout import notify, show_error


@st.dialog('Enrol a student')
def dialog_enroll(db, subject):
    st.write('Use the email the student will use to sign up. Existing student profiles are reused.')
    with st.form('enroll_student'):
        name = st.text_input('Full name', max_chars=100)
        email = st.text_input('Student email')
        save = st.form_submit_button('Enrol student', type='primary', width='stretch')
    if save:
        try:
            db.enroll(subject['id'], name, email)
            notify('Student enrolled. Add their face photo from the roster.')
            st.rerun()
        except Exception as error:
            show_error(error)

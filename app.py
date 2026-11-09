"""TeachUs Streamlit entry point."""
import streamlit as st
from src.components.header import header
from src.components.footer import footer
from src.database.db import get_db
from src.database.config import use_supabase
from src.screens.home_screen import home_screen
from src.screens.teacher_screen import teacher_screen
from src.screens.student_screen import student_screen
from src.ui.base_layout import setup, notices, show_error

setup()
header()
notices()
user = st.session_state.get('user')
db = None
try:
    db = get_db(user)
    if user:
        with st.sidebar:
            st.subheader('Your workspace')
            st.write(user['name'])
            st.caption(f"{user['role'].title()} · {user['email']}")
            if st.button('Sign out', width='stretch'):
                st.session_state.clear()
                st.rerun()
            st.divider()
            st.caption('Cloud database connected' if use_supabase() else 'Local storage · this device')
        if user['role'] == 'teacher':
            teacher_screen(db, user)
        else:
            student_screen(db, user)
    else:
        home_screen(db)
except Exception as error:
    show_error(error)
finally:
    if db:
        db.close()
footer()

"""Role entry and email/password authentication."""
import time
import streamlit as st
from src.ui.base_layout import notify, show_error


def home_screen(db):
    st.markdown('<div class="eyebrow">YOUR CLASSROOM, CONNECTED</div>', unsafe_allow_html=True)
    st.markdown('''<div class="hero"><h1>Be present.<br>Make every class count.</h1>
    <p>One welcoming space for your subjects, your students, and every day of learning.
    Take attendance with photos or a voice roll call, then review it together.</p></div>''',
                unsafe_allow_html=True)
    left, right = st.columns([1.05, 1], gap='large')
    with left:
        with st.container(border=True):
            st.subheader('A little less admin.')
            st.write('📸 **Photo attendance** · Match the class to your enrolled student photos.')
            st.write('🎙️ **Voice roll call** · Read out names and review the suggestions.')
            st.write('📊 **Clear records** · Follow attendance over time and export it anytime.')
        st.caption('Teachers manage classes. Students join with a code and follow their own progress.')
    with right:
        with st.container(border=True):
            role = st.radio('I am a', ['Teacher', 'Student'], horizontal=True, key='entry_role')
            login, signup = st.tabs(['Sign in', 'Create account'])
            with login:
                with st.form('signin'):
                    email = st.text_input('Email', key='login_email', placeholder='you@example.com')
                    password = st.text_input('Password', type='password', key='login_password')
                    submitted = st.form_submit_button('Sign in', type='primary', width='stretch')
                if submitted:
                    try:
                        retry = st.session_state.get('auth_retry', 0)
                        if time.monotonic() < retry:
                            raise ValueError('Please wait a few seconds before trying again.')
                        user = db.user(email, password)
                        if not user or user['role'] != role.lower():
                            st.session_state['auth_retry'] = time.monotonic() + 3
                            raise ValueError('Email, password, or selected account type is incorrect.')
                        st.session_state['user'] = user
                        notify(f"Welcome back, {user['name']}.")
                        st.rerun()
                    except Exception as error:
                        show_error(error)
            with signup:
                with st.form('signup'):
                    name = st.text_input('Full name', key='signup_name', max_chars=100)
                    email = st.text_input('Email', key='signup_email')
                    password = st.text_input('Password (at least 8 characters)', type='password', key='signup_password')
                    confirm = st.text_input('Confirm password', type='password')
                    submit = st.form_submit_button(f'Create {role.lower()} account', type='primary', width='stretch')
                if submit:
                    try:
                        if password != confirm:
                            raise ValueError('Passwords do not match.')
                        user = db.create_user(email, password, name, role.lower())
                        st.session_state['user'] = user
                        notify('Your account is ready.')
                        st.rerun()
                    except Exception as error:
                        show_error(error)

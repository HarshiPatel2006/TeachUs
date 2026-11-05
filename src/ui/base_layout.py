"""Shared page framing and restrained responsive styling."""
import streamlit as st


def setup():
    st.set_page_config(page_title='TeachUs · Attendance made simple', page_icon='🎓',
                       layout='wide', initial_sidebar_state='auto')
    st.markdown('''<style>
    .block-container {max-width:1180px;padding-top:2rem;padding-bottom:3rem}
    h1 {font-size:2.5rem!important;letter-spacing:-.055em;line-height:1.12!important}
    h2,h3 {letter-spacing:-.025em}
    [data-testid="stSidebar"] {border-right:1px solid #e6e8f2}
    [data-testid="stVerticalBlockBorderWrapper"] {border-radius:18px!important}
    [data-testid="stMetric"] {background:#eef0ff;padding:1rem;border-radius:14px}
    [data-testid="stMetricLabel"] {color:#5b6380}
    .brand {font-size:1.5rem;font-weight:800;letter-spacing:-.06em;color:#4f46e5}
    .eyebrow {color:#656a85;font-size:.78rem;letter-spacing:.12em;font-weight:700}
    .hero {padding:1.8rem 0 .8rem;max-width:760px}
    .hero p {font-size:1.13rem;color:#656a85;line-height:1.7}
    .footer {color:#757d94;font-size:.8rem;padding-top:2rem;border-top:1px solid #e6e8f2}
    div.stButton > button {border-radius:10px;min-height:2.65rem}
    [data-testid="stDialog"] h2 {font-size:1.5rem}
    @media(max-width:640px){.block-container{padding:1rem}h1{font-size:2rem!important}}
    </style>''', unsafe_allow_html=True)


def notify(message):
    st.session_state['_notice'] = message


def notices():
    if message := st.session_state.pop('_notice', None):
        st.toast(message, icon='✅')


def show_error(error):
    if isinstance(error, (ValueError, PermissionError)):
        st.error(str(error))
    else:
        import logging
        logging.getLogger(__name__).exception('TeachUs operation failed')
        st.error('This operation could not finish. Check the connection and server logs, then retry.')

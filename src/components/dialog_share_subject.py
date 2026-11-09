from urllib.parse import urlencode
import streamlit as st


@st.dialog('Invite your class')
def dialog_share_subject(subject):
    st.write(f"Share this code with students joining **{subject['name']}**.")
    st.code(subject['code'], language=None)
    try:
        base = st.secrets.get('APP_URL', '').strip().rstrip('/')
    except FileNotFoundError:
        base = ''
    link = (base or 'http://localhost:8501') + '/?' + urlencode({'join': subject['code']})
    st.caption('Use the copy button in the top-right corner of either box.')
    st.code(link, language=None)
    if not base:
        st.info('Set APP_URL in Streamlit secrets to share a public link. The join code works on any deployment.')

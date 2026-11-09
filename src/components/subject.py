import streamlit as st


def subject_card(subject, detail=''):
    with st.container(border=True):
        st.caption('SUBJECT')
        st.subheader(subject['name'])
        st.caption(detail or f"Join code · {subject['code']}")
        if st.button('Open subject →', key=f"open_{subject['id']}", width='stretch'):
            st.session_state['subject_id'] = subject['id']
            st.rerun()

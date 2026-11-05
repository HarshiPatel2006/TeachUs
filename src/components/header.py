from pathlib import Path
import streamlit as st


def header():
    logo = Path(__file__).resolve().parents[2] / 'img' / 'logo.png'
    left, right = st.columns([1, 14], vertical_alignment='center')
    with left:
        st.image(str(logo), width=44)
    with right:
        st.markdown('<div class="brand">TeachUs</div>', unsafe_allow_html=True)
    st.divider()

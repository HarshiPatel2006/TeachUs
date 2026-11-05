"""Compact brand header that stays on one line on mobile."""
import base64
from pathlib import Path
import streamlit as st


def header():
    logo = Path(__file__).resolve().parents[2] / 'img' / 'logo.png'
    encoded = base64.b64encode(logo.read_bytes()).decode('ascii')
    st.markdown(f'''<div style="display:flex;align-items:center;gap:14px">
      <img src="data:image/png;base64,{encoded}" width="40" height="40" alt="TeachUs graduation cap">
      <span class="brand">TeachUs</span></div>''', unsafe_allow_html=True)
    st.divider()

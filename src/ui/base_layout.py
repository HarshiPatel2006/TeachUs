import streamlit as st
def setup():
 st.set_page_config(page_title='TeachUs',page_icon='📚',layout='wide');st.markdown('<style>.block-container{max-width:1100px;padding-top:2rem}.brand{font-size:2.1rem;font-weight:800;color:#4f46e5}.muted{color:#64748b}</style>',unsafe_allow_html=True)
def header():st.markdown('<div class="brand">📚 TeachUs</div><p class="muted">Simple, fair attendance for every classroom.</p>',unsafe_allow_html=True)
def footer():st.divider();st.caption('TeachUs · Learn together, show up together')

import streamlit as st
def setup():
 st.set_page_config(page_title='TeachUs',page_icon='🎓'); st.markdown('<style>.block-container{max-width:900px;padding-top:2rem}.card{padding:1rem;border:1px solid #ddd;border-radius:12px}</style>',unsafe_allow_html=True)
def header(): st.title('🎓 TeachUs'); st.caption('Simple, private classroom attendance')
def footer(): st.caption('TeachUs • attendance made easy')

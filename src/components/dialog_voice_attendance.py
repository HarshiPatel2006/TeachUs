import streamlit as st
from src.pipelines.voice_pipeline import transcribe
@st.dialog('Voice attendance')
def voice_attendance_dialog(db,subject_id,names):
 audio=st.audio_input('Record roll call')
 if audio:
  text=transcribe(audio);st.write('Heard:',text);st.caption('Review and save the detected names.')

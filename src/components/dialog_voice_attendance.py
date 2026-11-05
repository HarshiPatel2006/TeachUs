from pathlib import Path
import tempfile
import streamlit as st
from src.components.dialog_attendance_results import queue_results
from src.pipelines.voice_pipeline import match_names, transcribe
from src.ui.base_layout import show_error


@st.dialog('Voice attendance', width='large')
def dialog_voice_attendance(db, subject, students):
    st.write('Read the full names of students who are present, with a short pause between names.')
    st.caption('English roll calls work best. Only say present students’ names; avoid saying absent names.')
    audio = st.audio_input('Record roll call', sample_rate=16000)
    upload = st.file_uploader('Or upload a roll call', type=['wav', 'mp3', 'm4a', 'ogg'], key='voice_upload')
    recording = audio or upload
    if st.button('Transcribe and match', type='primary', disabled=not recording):
        temporary = None
        try:
            if recording.size > 10 * 1024 * 1024:
                raise ValueError('Use an audio file below 10 MB.')
            with st.spinner('Transcribing… First use downloads the tiny speech model.'):
                with tempfile.NamedTemporaryFile(suffix='.audio', delete=False) as output:
                    temporary = Path(output.name)
                    output.write(recording.getvalue())
                heard = transcribe(temporary)
            if not heard:
                raise ValueError('No speech was heard. Try recording again closer to the microphone.')
            matched = match_names(heard, [s['name'] for s in students])
            queue_results(subject['id'], students, {s['id'] for s in students if s['name'] in matched},
                          'voice', f'Heard: {heard}')
            st.rerun()
        except Exception as error:
            show_error(error)
        finally:
            if temporary:
                temporary.unlink(missing_ok=True)

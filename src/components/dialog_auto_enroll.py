import hashlib
import streamlit as st
from src.pipelines.face_pipeline import detect_and_embed
from src.ui.base_layout import notify, show_error


@st.dialog('Enrol from a group photo', width='large')
def dialog_auto_enroll(db, subject):
    st.write('Detect faces, then assign each one a name and email. No identity is guessed automatically.')
    upload = st.file_uploader('Group photo', type=['jpg', 'jpeg', 'png'], key='auto_group_photo')
    camera = st.camera_input('Or take a group photo', key='auto_group_camera')
    image = camera or upload
    slot = f"auto_faces_{subject['id']}"
    if st.button('Find faces', type='primary', disabled=image is None):
        try:
            with st.spinner('Finding faces…'):
                faces = detect_and_embed(image)
            if not faces:
                raise ValueError('No clear faces found. Try a brighter, closer photo.')
            st.session_state[slot] = {'hash': hashlib.sha256(image.getvalue()).hexdigest(), 'faces': faces}
        except Exception as error:
            show_error(error)
    result = st.session_state.get(slot)
    if not result or not image or result['hash'] != hashlib.sha256(image.getvalue()).hexdigest():
        return
    st.caption('Review every selected face. Leave unselected faces out of the roster.')
    with st.form('confirm_group_enrollment'):
        entries = []
        for index, face in enumerate(result['faces']):
            with st.container(border=True):
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.image(face['photo'], width=100)
                with col2:
                    include = st.checkbox(f'Enrol face {index + 1}', key=f'auto_include_{index}')
                    name = st.text_input('Full name', key=f'auto_name_{index}', max_chars=100)
                    email = st.text_input('Email', key=f'auto_email_{index}')
                entries.append((include, name, email, face))
        consent = st.checkbox('I have permission to store these students’ face photos.')
        save = st.form_submit_button('Save selected students', type='primary')
    if save:
        try:
            selected = [e for e in entries if e[0]]
            if not selected or not consent:
                raise ValueError('Select at least one face and confirm permission.')
            emails = [db._email(e[2]) for e in selected]
            if len(set(emails)) != len(emails) or any(not e[1].strip() for e in selected):
                raise ValueError('Each selected face needs a name and a different email.')
            # Mark successes individually: retries after a connection failure skip completed faces.
            completed = result.setdefault('completed', [])
            for include, name, email, face in selected:
                fingerprint = hashlib.sha256(face['photo']).hexdigest()
                if fingerprint in completed:
                    continue
                student = db.enroll(subject['id'], name, email)
                db.add_photo(student['id'], face['photo'], face['embedding'], subject['id'])
                completed.append(fingerprint)
            st.session_state.pop(slot, None)
            notify(f'{len(selected)} students enrolled with face photos.')
            st.rerun()
        except Exception as error:
            show_error(error)

import streamlit as st
from src.pipelines.face_pipeline import detect_and_embed
from src.ui.base_layout import notify, show_error


@st.dialog('Add face photos', width='large')
def dialog_add_photo(db, student, subject_id=None):
    st.write(f"Add a clear, single-person photo for **{student['name']}**. Different angles help matching.")
    st.caption('Face photos and embeddings are stored privately. Only add photos with the student’s consent.')
    choice = st.radio('Photo source', ['Upload', 'Camera'], horizontal=True, key='add_photo_source')
    images = []
    if choice == 'Upload':
        images = st.file_uploader('Choose up to five face photos', type=['jpg', 'jpeg', 'png'],
                                  accept_multiple_files=True, key='enrollment_photos')
    else:
        camera = st.camera_input('Take a face photo', key='enrollment_camera')
        if camera:
            images = [camera]
    if st.button('Check and save photos', type='primary', disabled=not images):
        try:
            if len(images) > 5:
                raise ValueError('Choose at most five photos at once.')
            with st.spinner('Checking faces… First use downloads the recognition models.'):
                faces = []
                for image in images:
                    detected = detect_and_embed(image)
                    if len(detected) != 1:
                        raise ValueError(f'{image.name}: found {len(detected)} faces. Use one person per photo.')
                    faces.append(detected[0])
                for face in faces:
                    db.add_photo(student['id'], face['photo'], face['embedding'], subject_id)
            notify(f'{len(faces)} face photo(s) saved.')
            st.rerun()
        except Exception as error:
            show_error(error)

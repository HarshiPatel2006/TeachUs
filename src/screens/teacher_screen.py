"""Teacher subject workspace: roster, reviewed captures and exportable history."""
from datetime import date, timedelta
import pandas as pd
import streamlit as st
from src.components.subject import subject_card
from src.components.dialog_create_subject import dialog_create_subject
from src.components.dialog_share_subject import dialog_share_subject
from src.components.dialog_enroll import dialog_enroll
from src.components.dialog_auto_enroll import dialog_auto_enroll
from src.components.dialog_add_photo import dialog_add_photo
from src.components.dialog_voice_attendance import dialog_voice_attendance
from src.components.dialog_attendance_results import dialog_attendance_results, queue_results
from src.pipelines.face_pipeline import recognize_photos
from src.ui.base_layout import show_error


def history(db, subject):
    st.subheader('Attendance history')
    a, b = st.columns(2)
    start = a.date_input('From', date.today() - timedelta(days=30), key='history_start')
    end = b.date_input('To', date.today(), key='history_end')
    if start > end:
        st.error('The start date must come before the end date.')
        return
    rows = db.attendance(subject['id'], start, end)
    if not rows:
        st.info('No attendance in this date range. Try a wider range or save your first roll call.')
        return
    frame = pd.DataFrame(rows)
    st.dataframe(frame[['date', 'name', 'email', 'present', 'source', 'overridden']],
                 hide_index=True, width='stretch', column_config={
                     'present': st.column_config.CheckboxColumn('Present'),
                     'overridden': st.column_config.CheckboxColumn('Manually corrected')})
    st.download_button('Download CSV', db.attendance_csv(subject['id'], start, end),
                       f"attendance-{subject['code']}-{start}-{end}.csv", 'text/csv')


def photo_attendance(db, subject, students):
    st.subheader('Capture the class')
    st.write('Upload one or more class photos or take a photo now. Each recognised student is counted once.')
    mode = st.radio('Photo source', ['Upload photos', 'Camera'], horizontal=True, key='attendance_source')
    images = []
    if mode == 'Upload photos':
        images = st.file_uploader('Class photos', type=['jpg', 'jpeg', 'png'],
                                  accept_multiple_files=True, key=f"class_photos_{subject['id']}")
    else:
        camera = st.camera_input('Take a class photo', key=f"class_camera_{subject['id']}")
        if camera:
            images = [camera]
    if st.button('Match faces and review', type='primary', disabled=not images or not students):
        try:
            if len(images) > 10:
                raise ValueError('Use at most ten photos in one attendance capture.')
            candidates = [(s['id'], vector) for s in students
                          for vector in db.embeddings(s['id'], subject['id'])]
            if not candidates:
                raise ValueError('Add student face photos in the roster first.')
            with st.spinner('Recognising faces… First use downloads the models.'):
                present, detected, unknown = recognize_photos(images, candidates)
            if not detected:
                raise ValueError('No faces found. Try a brighter photo with faces closer to the camera.')
            queue_results(subject['id'], students, present, 'face',
                          f'{detected} faces detected · {len(present)} students matched · '
                          f'{unknown} faces unrecognised or ambiguous. Review all absent suggestions.')
            st.rerun()
        except Exception as error:
            show_error(error)


def teacher_screen(db, user):
    subjects = db.subjects()
    selected = st.session_state.get('subject_id')
    if not selected:
        st.caption('TEACHER WORKSPACE')
        st.title(f"Hello, {user['name'].split()[0]}.")
        st.write('Your classes, ready for a great day of learning.')
        a, b = st.columns([3, 1])
        a.metric('Your subjects', len(subjects))
        if b.button('＋ Create subject', type='primary', width='stretch'):
            dialog_create_subject(db)
        st.subheader('Your subjects')
        if not subjects:
            st.info('Start with a subject. Then invite students and build your class roster.')
        for offset in range(0, len(subjects), 3):
            columns = st.columns(3)
            for column, subject in zip(columns, subjects[offset:offset + 3]):
                with column:
                    subject_card(subject, f"{len(db.students(subject['id']))} students · {subject['code']}")
        return
    subject = db.subject(selected)
    if st.button('← All subjects'):
        st.session_state.pop('subject_id', None)
        st.session_state.pop('attendance_review', None)
        st.rerun()
    st.caption('SUBJECT WORKSPACE')
    st.title(subject['name'])
    st.caption(f"Join code · {subject['code']}")
    if st.button('Share subject'):
        dialog_share_subject(subject)
    students = db.students(selected)
    a, b = st.columns(2)
    a.metric('Students enrolled', len(students))
    b.metric('Students with face photos', sum(bool(db.embeddings(s['id'], selected)) for s in students))
    capture, roster, records = st.tabs(['Take attendance', 'Class roster', 'History & export'])
    with capture:
        if not students:
            st.info('Enrol students in the Class roster tab to begin taking attendance.')
        else:
            photo_attendance(db, subject, students)
            st.divider()
            a, b = st.columns(2)
            if a.button('🎙️ Take voice attendance', width='stretch'):
                dialog_voice_attendance(db, subject, students)
            if b.button('Review a manual roll call', width='stretch'):
                queue_results(selected, students, set(), 'manual', 'Enable manual overrides to mark students present.')
                st.rerun()
    with roster:
        a, b = st.columns(2)
        if a.button('＋ Enrol a student', width='stretch'):
            dialog_enroll(db, subject)
        if b.button('Enrol from group photo', width='stretch'):
            dialog_auto_enroll(db, subject)
        if not students:
            st.info('Your roster is empty. Enrol students here or share the subject code.')
        for student in students:
            with st.container(border=True):
                a, b = st.columns([3, 1], vertical_alignment='center')
                a.write(f"**{student['name']}**")
                a.caption(student['email'])
                count = len(db.embeddings(student['id'], selected))
                a.caption(f'{count} face photo(s)' if count else 'No face photos yet')
                if b.button('Add photos', key=f"photos_{student['id']}", width='stretch'):
                    dialog_add_photo(db, student, selected)
    with records:
        history(db, subject)
    review = st.session_state.get('attendance_review')
    if review and review['subject_id'] == selected:
        dialog_attendance_results(db, review)

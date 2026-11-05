from datetime import date
import uuid
import pandas as pd
import streamlit as st
from src.ui.base_layout import notify, show_error


def queue_results(subject_id, students, present, source, detail=''):
    st.session_state['attendance_review'] = {
        'subject_id': subject_id, 'students': students, 'present': list(present),
        'source': source, 'detail': detail, 'id': str(uuid.uuid4()),
    }


@st.dialog('Review attendance', width='large')
def dialog_attendance_results(db, review):
    st.write('Check the suggestions before saving. You can correct every student’s status.')
    if review.get('detail'):
        st.info(review['detail'])
    original = {s['id']: s['id'] in review['present'] for s in review['students']}
    frame = pd.DataFrame([{'Student': s['name'], 'Email': s['email'], 'Present': original[s['id']]}
                          for s in review['students']])
    if frame.empty:
        st.info('Enrol students before taking attendance.')
        return
    left, right = st.columns(2)
    left.metric('Suggested present', sum(original.values()))
    right.metric('Suggested absent', len(original) - sum(original.values()))
    allow_override = st.toggle('Enable manual overrides', value=False, key=f"override_{review['id']}")
    edited = st.data_editor(frame, hide_index=True, width='stretch',
                            disabled=['Student', 'Email'] if allow_override else True,
                            column_config={'Present': st.column_config.CheckboxColumn('Present')},
                            key=f"review_editor_{review['id']}")
    day = st.date_input('Attendance date', value=date.today(), max_value=date.today())
    st.caption('Saving again on the same date replaces that day’s attendance for this subject.')
    confirmed = st.checkbox('I have reviewed this attendance and the selected date.')
    if st.button('Save attendance', type='primary', disabled=not confirmed):
        try:
            records = {student['id']: bool(edited.iloc[index]['Present']) if allow_override else original[student['id']]
                       for index, student in enumerate(review['students'])}
            overrides = {sid for sid in records if records[sid] != original[sid]}
            db.take_attendance(review['subject_id'], records, review['source'], day, overrides)
            st.session_state.pop('attendance_review', None)
            notify('Attendance saved.')
            st.rerun()
        except Exception as error:
            show_error(error)
    if st.button('Discard results'):
        st.session_state.pop('attendance_review', None)
        st.rerun()

"""Student joining and private attendance history."""
import pandas as pd
import streamlit as st
from src.components.subject import subject_card
from src.components.dialog_add_photo import dialog_add_photo
from src.ui.base_layout import notify, show_error


def student_screen(db, user):
    st.caption('STUDENT WORKSPACE')
    st.title(f"Hello, {user['name'].split()[0]}.")
    st.write('Stay connected to your classes and see every day of progress.')
    with st.expander('Join a subject', expanded=not db.subjects() or bool(st.query_params.get('join'))):
        with st.form('join_subject'):
            code = st.text_input('Subject join code', value=st.query_params.get('join', ''), max_chars=12,
                                 placeholder='Enter the code from your teacher')
            submit = st.form_submit_button('Join subject', type='primary')
        if submit:
            try:
                subject = db.join(code)
                st.query_params.clear()
                notify(f"You joined {subject['name']}.")
                st.rerun()
            except Exception as error:
                show_error(error)
    a, b = st.columns([3, 1])
    a.caption('Add clear photos so your teacher can recognise you in class photos.')
    if b.button('Add my face photos', width='stretch'):
        dialog_add_photo(db, db.own_student())
    subjects = db.subjects()
    selected = st.session_state.get('subject_id')
    if selected:
        subject = db.subject(selected)
        if st.button('← All subjects'):
            st.session_state.pop('subject_id', None)
            st.rerun()
        st.subheader(subject['name'])
        rows = db.attendance(selected)
        if not rows:
            st.info('Your teacher has not saved any attendance yet. Your history will appear here.')
        else:
            count = sum(bool(r['present']) for r in rows)
            a, b, c = st.columns(3)
            a.metric('Attendance', f'{100 * count / len(rows):.0f}%')
            b.metric('Classes present', count)
            c.metric('Classes recorded', len(rows))
            st.caption('Percentage counts the days recorded by your teacher since you joined the roster.')
            st.dataframe(pd.DataFrame(rows)[['date', 'present', 'source']], hide_index=True,
                         width='stretch', column_config={'present': st.column_config.CheckboxColumn('Present')})
            st.download_button('Download my history', db.attendance_csv(selected),
                               f"my-attendance-{subject['code']}.csv", 'text/csv')
        return
    st.subheader('Your subjects')
    if not subjects:
        st.info('No subjects yet. Ask your teacher for a join code and enter it above.')
    for offset in range(0, len(subjects), 3):
        columns = st.columns(3)
        for column, subject in zip(columns, subjects[offset:offset + 3]):
            rows = db.attendance(subject['id'])
            detail = (f"{sum(bool(r['present']) for r in rows) / len(rows):.0%} attendance · {len(rows)} classes"
                      if rows else 'No attendance recorded yet')
            with column:
                subject_card(subject, detail)

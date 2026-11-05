import streamlit as st
@st.dialog('Attendance results')
def attendance_results_dialog(db,subject_id,records):
 ids=list(records);overrides=set();st.dataframe(records)
 for uid in ids:
  if st.checkbox('Override present',value=records[uid],key=f'override{uid}'):overrides.add(uid)
 if st.button('Save attendance',type='primary'):db.take_attendance(subject_id,records,overrides=overrides);st.success('Saved');st.rerun()

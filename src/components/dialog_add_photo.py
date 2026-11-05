import streamlit as st
@st.dialog('Add face photo')
def add_photo_dialog(db,student_id):
 photo=st.camera_input('Take a face photo') or st.file_uploader('Upload photo',type=['jpg','jpeg','png'])
 if photo and st.button('Save photo'):db.add_photo(student_id,path=photo.name);st.success('Photo saved')

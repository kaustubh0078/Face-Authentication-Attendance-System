"""
Face Authentication Attendance System
Main Streamlit Application

Features:
- Register users with face capture
- Mark attendance with face recognition
- View attendance records
"""
import streamlit as st
import cv2
import numpy as np
from datetime import date, datetime, timedelta
import time
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    APP_TITLE, FACE_IMAGES_DIR, CAMERA_INDEX, 
    RECOGNITION_THRESHOLD
)
from modules.database import DatabaseManager
from modules.face_detector import FaceDetector
from modules.face_matcher import FaceMatcher
from utils.image_preprocessing import preprocess_frame, get_image_quality_score
from utils.helpers import (
    format_timestamp, format_time_only, calculate_work_hours,
    get_greeting, is_valid_employee_id, is_valid_name,
    get_punch_status_emoji
)

# Page configuration
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="👤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize session state variables"""
    if 'db' not in st.session_state:
        st.session_state.db = DatabaseManager()
    if 'detector' not in st.session_state:
        st.session_state.detector = FaceDetector()
    if 'matcher' not in st.session_state:
        st.session_state.matcher = FaceMatcher(threshold=RECOGNITION_THRESHOLD)
    if 'captured_frame' not in st.session_state:
        st.session_state.captured_frame = None
    if 'captured_encoding' not in st.session_state:
        st.session_state.captured_encoding = None
    if 'last_recognition' not in st.session_state:
        st.session_state.last_recognition = None


def load_known_faces():
    """Load all known face encodings into matcher"""
    users = st.session_state.db.get_all_users()
    st.session_state.matcher.load_known_faces(users)


def main():
    """Main application entry point"""
    init_session_state()
    load_known_faces()
    
    # Sidebar navigation
    st.sidebar.markdown(f"## 👤 {APP_TITLE}")
    st.sidebar.markdown("---")
    
    page = st.sidebar.radio(
        "Navigation",
        ["🏠 Dashboard", "📝 Register User", "✅ Mark Attendance", "📊 Attendance History", "⚙️ Settings"],
        label_visibility="collapsed"
    )
    
    # Display current stats in sidebar
    users = st.session_state.db.get_all_users()
    st.sidebar.markdown("---")
    st.sidebar.metric("Registered Users", len(users))
    
    today_summary = st.session_state.db.get_today_attendance_summary()
    present_count = sum(1 for s in today_summary if s['first_in'])
    st.sidebar.metric("Present Today", present_count)
    
    # Route to appropriate page
    if page == "🏠 Dashboard":
        show_dashboard()
    elif page == "📝 Register User":
        show_registration()
    elif page == "✅ Mark Attendance":
        show_attendance()
    elif page == "📊 Attendance History":
        show_history()
    elif page == "⚙️ Settings":
        show_settings()


def show_dashboard():
    """Dashboard page with overview statistics"""
    st.markdown(f"<h1 class='main-header'>🏠 {get_greeting()}! Welcome to Attendance System</h1>", unsafe_allow_html=True)
    
    st.subheader("📊 Today's Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    summary = st.session_state.db.get_today_attendance_summary()
    users = st.session_state.db.get_all_users()
    
    total_users = len(users)
    present = sum(1 for s in summary if s['first_in'])
    absent = total_users - present
    checked_out = sum(1 for s in summary if s['last_out'])
    
    with col1:
        st.metric("👥 Total Users", total_users)
    with col2:
        st.metric("🟢 Present", present)
    with col3:
        st.metric("🔴 Absent", absent)
    with col4:
        st.metric("✅ Checked Out", checked_out)
    
    st.markdown("---")
    
    st.subheader("📋 Today's Attendance Status")
    
    if not summary:
        st.info("No users registered yet. Go to Register User to add users.")
    else:
        for item in summary:
            status = "🟢 Present" if item['first_in'] else "🔴 Not arrived"
            punch_in = format_time_only(item['first_in']) if item['first_in'] else "-"
            punch_out = format_time_only(item['last_out']) if item['last_out'] else "-"
            work_hours = calculate_work_hours(item['first_in'], item['last_out']) or "-"
            
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 2, 1.5, 1.5, 1.5])
                with col1:
                    st.write(f"**{item['name']}**")
                with col2:
                    st.write(f"ID: {item['employee_id']}")
                with col3:
                    st.write(f"In: {punch_in}")
                with col4:
                    st.write(f"Out: {punch_out}")
                with col5:
                    st.write(f"Hours: {work_hours}")


def show_registration():
    """User registration page"""
    st.markdown("<h1 class='main-header'>📝 Register New User</h1>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📋 User Information")
        
        name = st.text_input("Full Name", placeholder="Enter full name")
        employee_id = st.text_input("Employee ID", placeholder="Enter unique employee ID")
        
        name_valid, name_error = is_valid_name(name) if name else (False, "")
        emp_valid, emp_error = is_valid_employee_id(employee_id) if employee_id else (False, "")
        
        if name and not name_valid:
            st.error(name_error)
        if employee_id and not emp_valid:
            st.error(emp_error)
    
    with col2:
        st.subheader("📷 Face Capture")
        
        img_file = st.camera_input("Take a photo", key="registration_camera")
        
        if img_file is not None:
            file_bytes = np.asarray(bytearray(img_file.read()), dtype=np.uint8)
            frame = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            frame = preprocess_frame(frame)
            
            quality = get_image_quality_score(frame)
            
            if not quality['overall_ok']:
                st.warning("⚠️ Image quality could be better. Consider retaking with better lighting.")
            
            face_location = st.session_state.detector.detect_single_face(frame)
            
            if face_location is None:
                faces = st.session_state.detector.detect_faces(frame)
                if len(faces) > 1:
                    st.error("❌ Multiple faces detected. Please ensure only one face is visible.")
                else:
                    st.error("❌ No face detected. Please position your face clearly in the frame.")
            else:
                st.success("✅ Face detected successfully!")
                
                encoding = st.session_state.detector.get_face_encoding(frame, face_location)
                
                if encoding is not None:
                    st.session_state.captured_frame = frame
                    st.session_state.captured_encoding = encoding
    
    st.markdown("---")
    
    if st.button("✅ Register User", type="primary", use_container_width=True):
        if not name_valid:
            st.error(f"Invalid name: {name_error}")
        elif not emp_valid:
            st.error(f"Invalid employee ID: {emp_error}")
        elif st.session_state.captured_encoding is None:
            st.error("Please capture a face photo first!")
        else:
            try:
                image_filename = f"{employee_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                image_path = os.path.join(FACE_IMAGES_DIR, image_filename)
                cv2.imwrite(image_path, st.session_state.captured_frame)
                
                user_id = st.session_state.db.register_user(
                    name=name,
                    employee_id=employee_id,
                    face_encoding=st.session_state.captured_encoding,
                    image_path=image_path
                )
                
                load_known_faces()
                
                st.session_state.captured_frame = None
                st.session_state.captured_encoding = None
                
                st.success(f"✅ User '{name}' registered successfully with ID: {user_id}")
                st.balloons()
                
            except ValueError as e:
                st.error(f"❌ Registration failed: {str(e)}")
            except Exception as e:
                st.error(f"❌ An error occurred: {str(e)}")


def show_attendance():
    """Mark attendance page with face recognition"""
    st.markdown("<h1 class='main-header'>✅ Mark Attendance</h1>", unsafe_allow_html=True)
    
    if st.session_state.matcher.num_known_faces == 0:
        st.warning("⚠️ No users registered yet. Please register users first.")
        return
    
    st.info(f"👥 {st.session_state.matcher.num_known_faces} users registered in system")
    
    col1, col2 = st.columns([1.5, 1])
    
    with col1:
        st.subheader("📷 Camera Feed")
        
        img_file = st.camera_input("Look at the camera", key="attendance_camera")
        
        recognition_result = None
        
        if img_file is not None:
            file_bytes = np.asarray(bytearray(img_file.read()), dtype=np.uint8)
            frame = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            frame = preprocess_frame(frame)
            
            face_location = st.session_state.detector.detect_single_face(frame)
            
            if face_location is None:
                st.error("❌ No face detected or multiple faces found.")
            else:
                encoding = st.session_state.detector.get_face_encoding(frame, face_location)
                
                if encoding is not None:
                    user_id, name, distance = st.session_state.matcher.match_face(encoding)
                    confidence = st.session_state.matcher.get_match_confidence(distance)
                    
                    if user_id is not None:
                        recognition_result = {
                            'user_id': user_id,
                            'name': name,
                            'distance': distance,
                            'confidence': confidence,
                            'frame': frame,
                            'face_location': face_location
                        }
                        st.session_state.last_recognition = recognition_result
                        
                        st.success(f"✅ Recognized: **{name}** (Confidence: {confidence:.1f}%)")
                    else:
                        st.error(f"❌ Face not recognized (Best match: {confidence:.1f}%)")
                        
                        top_matches = st.session_state.matcher.find_all_matches(encoding, top_k=3)
                        if top_matches:
                            st.write("Closest matches:")
                            for uid, uname, dist, conf in top_matches:
                                st.write(f"  - {uname}: {conf:.1f}%")
    
    with col2:
        st.subheader("📊 Recognition Result")
        
        if recognition_result or st.session_state.last_recognition:
            result = recognition_result or st.session_state.last_recognition
            
            st.markdown(f"### 👤 {result['name']}")
            st.metric("Match Confidence", f"{result['confidence']:.1f}%")
            
            user = st.session_state.db.get_user_by_id(result['user_id'])
            if user:
                st.write(f"**Employee ID:** {user['employee_id']}")
                
                last_punch = st.session_state.db.get_last_punch(result['user_id'])
                next_punch = "OUT" if last_punch == "IN" else "IN"
                
                status_emoji = get_punch_status_emoji(last_punch)
                st.write(f"**Last Punch:** {status_emoji} {last_punch or 'None'}")
                
                st.markdown("---")
                
                if st.button(f"🕐 Punch {next_punch}", type="primary", use_container_width=True):
                    record_id = st.session_state.db.log_attendance(
                        user_id=result['user_id'],
                        punch_type=next_punch
                    )
                    
                    emoji = "🟢" if next_punch == "IN" else "🔴"
                    st.success(f"{emoji} Punch-{next_punch} recorded for {result['name']} at {datetime.now().strftime('%H:%M:%S')}")
                    st.balloons()
                    
                    st.session_state.last_recognition = None


def show_history():
    """Attendance history page"""
    st.markdown("<h1 class='main-header'>📊 Attendance History</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        users = st.session_state.db.get_all_users()
        user_options = {"All Users": None}
        user_options.update({u['name']: u['id'] for u in users})
        selected_user = st.selectbox("Filter by User", options=list(user_options.keys()))
        user_id = user_options[selected_user]
    
    with col2:
        date_from = st.date_input("From Date", value=date.today() - timedelta(days=7))
    
    with col3:
        date_to = st.date_input("To Date", value=date.today())
    
    history = st.session_state.db.get_attendance_history(
        user_id=user_id,
        date_from=date_from,
        date_to=date_to
    )
    
    st.markdown("---")
    
    if not history:
        st.info("No attendance records found for the selected criteria.")
    else:
        st.write(f"**Total Records:** {len(history)}")
        
        import pandas as pd
        
        df_data = []
        for record in history:
            df_data.append({
                "Date": format_timestamp(record['timestamp'], "%Y-%m-%d"),
                "Time": format_timestamp(record['timestamp'], "%H:%M:%S"),
                "Name": record['name'],
                "Employee ID": record['employee_id'],
                "Type": f"{'🟢' if record['punch_type'] == 'IN' else '🔴'} Punch-{record['punch_type']}"
            })
        
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"attendance_{date_from}_{date_to}.csv",
            mime="text/csv"
        )


def show_settings():
    """Settings page"""
    st.markdown("<h1 class='main-header'>⚙️ Settings</h1>", unsafe_allow_html=True)
    
    st.subheader("👥 User Management")
    
    users = st.session_state.db.get_all_users()
    
    if not users:
        st.info("No users registered yet.")
    else:
        for user in users:
            with st.expander(f"👤 {user['name']} ({user['employee_id']})"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**User ID:** {user['id']}")
                    st.write(f"**Registered:** {format_timestamp(user['registration_date'])}")
                    if user['image_path'] and os.path.exists(user['image_path']):
                        st.image(user['image_path'], width=150)
                
                with col2:
                    if st.button("🗑️ Delete", key=f"delete_{user['id']}", type="secondary"):
                        st.session_state.db.delete_user(user['id'])
                        if user['image_path'] and os.path.exists(user['image_path']):
                            os.remove(user['image_path'])
                        load_known_faces()
                        st.success(f"User {user['name']} deleted.")
                        st.rerun()
    
    st.markdown("---")
    
    st.subheader("ℹ️ System Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Recognition Threshold:** {RECOGNITION_THRESHOLD}")
        st.write(f"**Camera Index:** {CAMERA_INDEX}")
    
    with col2:
        st.write(f"**Total Users:** {len(users)}")
        st.write(f"**Database Path:** {st.session_state.db.db_path}")


if __name__ == "__main__":
    main()

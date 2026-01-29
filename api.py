"""
Flask API Backend for Face Authentication Attendance System
Provides REST endpoints for React frontend
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import cv2
import numpy as np
import base64
import os
from datetime import datetime, date, timedelta

# Import existing modules
from modules.database import DatabaseManager
from modules.face_detector import FaceDetector
from modules.face_matcher import FaceMatcher
from utils.image_preprocessing import preprocess_frame
from config import FACE_IMAGES_DIR, RECOGNITION_THRESHOLD, FLASK_DEBUG, FLASK_HOST, FLASK_PORT, FRONTEND_URL

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": FRONTEND_URL}})  # Enable CORS for React frontend

# Initialize components
db = DatabaseManager()
detector = FaceDetector()
matcher = FaceMatcher(threshold=RECOGNITION_THRESHOLD)


def load_known_faces():
    """Load all known face encodings into matcher"""
    try:
        users = db.get_all_users()
        matcher.load_known_faces(users)
        print(f"Loaded {len(users)} users based on existing database.")
    except Exception as e:
        print(f"Warning: Could not load users on startup. Database might be empty. Error: {e}")


def decode_base64_image(base64_string):
    """Decode base64 image to OpenCV format"""
    # Remove data URL prefix if present
    if ',' in base64_string:
        base64_string = base64_string.split(',')[1]
    
    img_bytes = base64.b64decode(base64_string)
    img_array = np.frombuffer(img_bytes, dtype=np.uint8)
    frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    return frame


# ======================
# USER ENDPOINTS
# ======================

@app.route('/api/users', methods=['GET'])
def get_users():
    """Get all registered users"""
    try:
        users = db.get_all_users()
        result = []
        for user in users:
            result.append({
                'id': user['id'],
                'name': user['name'],
                'employee_id': user['employee_id'],
                'registration_date': user['registration_date'],
                'image_path': user['image_path']
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/users', methods=['POST'])
def register_user():
    """Register a new user with face"""
    data = request.json
    
    name = data.get('name')
    employee_id = data.get('employee_id')
    image_base64 = data.get('image')
    
    if not all([name, employee_id, image_base64]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    try:
        # Decode image
        frame = decode_base64_image(image_base64)
        frame = preprocess_frame(frame)
        
        # Detect face
        face_location = detector.detect_single_face(frame)
        
        if face_location is None:
            faces = detector.detect_faces(frame)
            if len(faces) > 1:
                return jsonify({'error': 'Multiple faces detected'}), 400
            return jsonify({'error': 'No face detected'}), 400
        
        # Get encoding
        encoding = detector.get_face_encoding(frame, face_location)
        
        if encoding is None:
            return jsonify({'error': 'Could not generate face encoding'}), 400
        
        # Save image
        image_filename = f"{employee_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        image_path = os.path.join(FACE_IMAGES_DIR, image_filename)
        cv2.imwrite(image_path, frame)
        
        # Register user
        user_id = db.register_user(
            name=name,
            employee_id=employee_id,
            face_encoding=encoding,
            image_path=image_path
        )
        
        # Reload known faces
        load_known_faces()
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'message': f'User {name} registered successfully'
        })
        
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Error registering user: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Check permissions/path info for debugging
        try:
            print(f"Current working directory: {os.getcwd()}")
            print(f"Target image path: {FACE_IMAGES_DIR}")
            print(f"Directory exists: {os.path.exists(FACE_IMAGES_DIR)}")
            print(f"Directory writable: {os.access(FACE_IMAGES_DIR, os.W_OK)}")
        except:
            pass
            
        return jsonify({'error': f"Server Error: {str(e)}"}), 500


@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    """Delete a user"""
    try:
        user = db.get_user_by_id(user_id)
        if user and user['image_path'] and os.path.exists(user['image_path']):
            try:
                os.remove(user['image_path'])
            except OSError:
                pass  # Ignore if file doesn't exist/can't be deleted
        
        db.delete_user(user_id)
        load_known_faces()
        
        return jsonify({'success': True, 'message': 'User deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ======================
# RECOGNITION ENDPOINTS
# ======================

@app.route('/api/recognize', methods=['POST'])
def recognize_face():
    """Recognize face and optionally log attendance"""
    data = request.json
    
    image_base64 = data.get('image')
    log_attendance = data.get('log_attendance', False)
    
    if not image_base64:
        return jsonify({'error': 'No image provided'}), 400
    
    try:
        # Decode image
        frame = decode_base64_image(image_base64)
        frame = preprocess_frame(frame)
        
        # Detect face
        face_location = detector.detect_single_face(frame)
        
        if face_location is None:
            return jsonify({'recognized': False, 'error': 'No face detected'}), 200
        
        # Get encoding
        encoding = detector.get_face_encoding(frame, face_location)
        
        if encoding is None:
            return jsonify({'recognized': False, 'error': 'Could not process face'}), 200
        
        # Ensure matcher has latest faces
        # load_known_faces() # creating performance bottleneck, call less frequently
        
        # Match face
        user_id, name, distance = matcher.match_face(encoding)
        confidence = float(matcher.get_match_confidence(distance))
        
        if user_id is not None:
            user = db.get_user_by_id(user_id)
            last_punch = db.get_last_punch(user_id)
            next_punch = "OUT" if last_punch == "IN" else "IN"
            
            result = {
                'recognized': True,
                'user_id': user_id,
                'name': name,
                'employee_id': user['employee_id'],
                'confidence': round(confidence, 1),
                'last_punch': last_punch,
                'next_punch': next_punch
            }
            
            # Log attendance if requested
            if log_attendance:
                record_id = db.log_attendance(user_id=user_id, punch_type=next_punch)
                result['attendance_logged'] = True
                result['punch_type'] = next_punch
                result['punch_time'] = datetime.now().strftime('%H:%M:%S')
            
            return jsonify(result)
        else:
            return jsonify({
                'recognized': False,
                'confidence': float(confidence),
                'error': 'Face not recognized'
            })
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/punch', methods=['POST'])
def punch_attendance():
    """Log attendance directly using user_id (after recognition)"""
    data = request.json
    
    user_id = data.get('user_id')
    punch_type = data.get('punch_type')  # Optional: 'IN' or 'OUT'
    
    if not user_id:
        return jsonify({'error': 'No user_id provided'}), 400
    
    try:
        user = db.get_user_by_id(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Use provided punch_type or auto-detect
        if not punch_type:
            last_punch = db.get_last_punch(user_id)
            punch_type = "OUT" if last_punch == "IN" else "IN"
        
        record_id = db.log_attendance(user_id=user_id, punch_type=punch_type)
        
        return jsonify({
            'success': True,
            'punch_type': punch_type,
            'punch_time': datetime.now().strftime('%H:%M:%S'),
            'name': user['name']
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ======================
# ATTENDANCE ENDPOINTS
# ======================

@app.route('/api/attendance', methods=['GET'])
def get_attendance():
    """Get attendance history"""
    user_id = request.args.get('user_id', type=int)
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    try:
        # Parse dates
        if date_from:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
        else:
            date_from = date.today() - timedelta(days=7)
        
        if date_to:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
        else:
            date_to = date.today()
        
        history = db.get_attendance_history(
            user_id=user_id,
            date_from=date_from,
            date_to=date_to
        )
        
        result = []
        for record in history:
            result.append({
                'id': record['id'],
                'user_id': record['user_id'],
                'name': record['name'],
                'employee_id': record['employee_id'],
                'punch_type': record['punch_type'],
                'timestamp': record['timestamp']
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/attendance/today', methods=['GET'])
def get_today_attendance():
    """Get today's attendance summary"""
    try:
        summary = db.get_today_attendance_summary()
        
        result = []
        for item in summary:
            # Calculate duration if both in and out exist
            duration = '-'
            if item['first_in'] and item['last_out']:
                try:
                    in_time = datetime.strptime(item['first_in'], '%Y-%m-%d %H:%M:%S')
                    out_time = datetime.strptime(item['last_out'], '%Y-%m-%d %H:%M:%S')
                    diff = out_time - in_time
                    hours = diff.seconds // 3600
                    minutes = (diff.seconds % 3600) // 60
                    duration = f"{hours}h {minutes}m"
                except:
                    duration = '-'
            
            # Determine status
            if item['last_out']:
                status = 'checked_out'
            elif item['first_in']:
                status = 'present'
            else:
                status = 'absent'
            
            # Format times
            in_time_str = '-'
            out_time_str = '-'
            if item['first_in']:
                try:
                    in_time_str = datetime.strptime(item['first_in'], '%Y-%m-%d %H:%M:%S').strftime('%H:%M:%S')
                except:
                    in_time_str = item['first_in']
            if item['last_out']:
                try:
                    out_time_str = datetime.strptime(item['last_out'], '%Y-%m-%d %H:%M:%S').strftime('%H:%M:%S')
                except:
                    out_time_str = item['last_out']
            
            # Get initials for avatar
            name_parts = item['name'].split()
            avatar = ''.join(p[0].upper() for p in name_parts[:2]) if name_parts else '?'
            
            # Assign colors based on index
            colors = ['bg-indigo-500', 'bg-emerald-500', 'bg-violet-500', 'bg-rose-500', 'bg-amber-500']
            color = colors[item['id'] % len(colors)]
            
            result.append({
                'id': item['employee_id'],
                'user_id': item['id'],
                'name': item['name'],
                'role': 'Employee',
                'avatar': avatar,
                'color': color,
                'status': status,
                'inTime': in_time_str,
                'outTime': out_time_str,
                'duration': duration
            })
        
        return jsonify(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ======================
# STATS ENDPOINT
# ======================

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get dashboard statistics"""
    try:
        users = db.get_all_users()
        summary = db.get_today_attendance_summary()
        
        total_users = len(users)
        present = sum(1 for s in summary if s['first_in'])
        checked_out = sum(1 for s in summary if s['last_out'])
        absent = total_users - present
        
        return jsonify({
            'totalUsers': total_users,
            'present': present,
            'absent': absent,
            'checkedOut': checked_out
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ======================
# HEALTH CHECK
# ======================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    # Load known faces on startup
    load_known_faces()
    
    print("=" * 50)
    print("Face Authentication API Server")
    print("=" * 50)
    print(f"Users loaded: {matcher.num_known_faces}")
    print(f"API running at: http://{FLASK_HOST}:{FLASK_PORT}")
    print("=" * 50)
    
    app.run(debug=FLASK_DEBUG, host=FLASK_HOST, port=FLASK_PORT)

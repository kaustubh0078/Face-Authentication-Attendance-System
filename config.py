"""
Configuration settings for Face Authentication Attendance System
Supports environment variables for production deployment
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Database settings
DATABASE_PATH = os.getenv('DATABASE_PATH', os.path.join(BASE_DIR, "data", "faces.db"))
FACE_IMAGES_DIR = os.path.join(BASE_DIR, "data", "face_images")

# Face Recognition settings
RECOGNITION_THRESHOLD = float(os.getenv('RECOGNITION_THRESHOLD', '0.25'))
FACE_DETECTION_MODEL = os.getenv('FACE_DETECTION_MODEL', 'opencv')
EMBEDDING_MODEL = "Facenet"

# Anti-Spoofing settings
EAR_THRESHOLD = 0.25
BLINK_CONSEC_FRAMES = 2
BLINK_TIMEOUT_SECONDS = 10
REQUIRE_BLINK_FOR_ATTENDANCE = True

# Camera settings
CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480

# Image preprocessing
ENABLE_LIGHTING_NORMALIZATION = True
CLAHE_CLIP_LIMIT = 2.0
CLAHE_TILE_SIZE = (8, 8)

# UI Settings
APP_TITLE = "Face Authentication Attendance System"
PRIMARY_COLOR = "#1f77b4"

# Flask settings
FLASK_ENV = os.getenv('FLASK_ENV', 'development')
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))

# CORS settings
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')

# Ensure directories exist
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
os.makedirs(FACE_IMAGES_DIR, exist_ok=True)

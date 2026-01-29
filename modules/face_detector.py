"""
Face Detection module for Face Authentication Attendance System
Uses OpenCV for face detection and histogram-based encoding
"""
import cv2
import numpy as np
from typing import List, Tuple, Optional
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import FACE_DETECTION_MODEL


class FaceDetector:
    """Handles face detection and encoding using OpenCV"""
    
    def __init__(self, detector_backend: str = "opencv"):
        """Initialize face detector"""
        self.detector_backend = detector_backend
        
        # Face cascade for detection
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        
        # Eye cascade for landmark detection
        self.eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_eye.xml'
        )
    
    def detect_faces(self, frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detect all faces in a frame
        
        Returns:
            List of face locations as (top, right, bottom, left) tuples
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.1, 
            minNeighbors=5,
            minSize=(80, 80)
        )
        
        locations = []
        for (x, y, w, h) in faces:
            locations.append((y, x + w, y + h, x))
        
        return locations
    
    def detect_single_face(self, frame: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """Detect a single face in frame (for registration)"""
        faces = self.detect_faces(frame)
        if len(faces) == 1:
            return faces[0]
        return None
    
    def get_face_encoding(self, frame: np.ndarray, 
                          face_location: Optional[Tuple[int, int, int, int]] = None) -> Optional[np.ndarray]:
        """
        Get face encoding using enhanced histogram and spatial features
        
        This method combines multiple feature types for better discrimination:
        - Spatial grid histograms (face divided into regions)
        - LBP texture features
        - Gradient orientation features
        """
        if face_location is None:
            faces = self.detect_faces(frame)
            if not faces:
                return None
            face_location = faces[0]
        
        # Crop and resize face to standard size
        top, right, bottom, left = face_location
        face = frame[top:bottom, left:right]
        
        if face.size == 0:
            return None
        
        # Resize to 96x96 for consistent feature extraction
        face = cv2.resize(face, (96, 96))
        gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
        
        # Apply histogram equalization for lighting invariance
        gray = cv2.equalizeHist(gray)
        
        features = []
        
        # 1. Spatial grid features - divide face into 4x4 grid
        grid_size = 4
        cell_h = 96 // grid_size
        cell_w = 96 // grid_size
        
        for i in range(grid_size):
            for j in range(grid_size):
                cell = gray[i*cell_h:(i+1)*cell_h, j*cell_w:(j+1)*cell_w]
                hist = cv2.calcHist([cell], [0], None, [16], [0, 256])
                hist = cv2.normalize(hist, hist).flatten()
                features.extend(hist)
        
        # 2. LBP features for texture
        lbp = self._compute_lbp(gray)
        lbp_hist = cv2.calcHist([lbp], [0], None, [59], [0, 59])  # 59 uniform patterns
        lbp_hist = cv2.normalize(lbp_hist, lbp_hist).flatten()
        features.extend(lbp_hist)
        
        # 3. HOG-like gradient features
        gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        mag, ang = cv2.cartToPolar(gx, gy)
        
        # Binned gradient orientations
        bins = 9
        ang_bins = (ang * bins / (2 * np.pi)).astype(np.int32) % bins
        
        for b in range(bins):
            mask = (ang_bins == b)
            features.append(np.sum(mag[mask]) / (mag.sum() + 1e-7))
        
        # 4. Key facial region features (eyes, nose, mouth areas)
        # Upper third (forehead/eyes)
        upper = gray[0:32, :]
        upper_hist = cv2.calcHist([upper], [0], None, [16], [0, 256])
        upper_hist = cv2.normalize(upper_hist, upper_hist).flatten()
        features.extend(upper_hist)
        
        # Middle third (nose/cheeks)
        middle = gray[32:64, :]
        middle_hist = cv2.calcHist([middle], [0], None, [16], [0, 256])
        middle_hist = cv2.normalize(middle_hist, middle_hist).flatten()
        features.extend(middle_hist)
        
        # Lower third (mouth/chin)
        lower = gray[64:96, :]
        lower_hist = cv2.calcHist([lower], [0], None, [16], [0, 256])
        lower_hist = cv2.normalize(lower_hist, lower_hist).flatten()
        features.extend(lower_hist)
        
        return np.array(features, dtype=np.float32)
    
    def _compute_lbp(self, gray: np.ndarray) -> np.ndarray:
        """Compute Local Binary Pattern"""
        rows, cols = gray.shape
        lbp = np.zeros((rows-2, cols-2), dtype=np.uint8)
        
        for i in range(1, rows-1):
            for j in range(1, cols-1):
                center = gray[i, j]
                code = 0
                code |= (gray[i-1, j-1] >= center) << 7
                code |= (gray[i-1, j] >= center) << 6
                code |= (gray[i-1, j+1] >= center) << 5
                code |= (gray[i, j+1] >= center) << 4
                code |= (gray[i+1, j+1] >= center) << 3
                code |= (gray[i+1, j] >= center) << 2
                code |= (gray[i+1, j-1] >= center) << 1
                code |= (gray[i, j-1] >= center) << 0
                lbp[i-1, j-1] = code
        
        return lbp
    
    def get_all_face_encodings(self, frame: np.ndarray) -> List[Tuple[Tuple[int, int, int, int], np.ndarray]]:
        """Get encodings for all faces in a frame"""
        locations = self.detect_faces(frame)
        results = []
        
        for loc in locations:
            encoding = self.get_face_encoding(frame, loc)
            if encoding is not None:
                results.append((loc, encoding))
        
        return results
    
    def get_face_landmarks(self, frame: np.ndarray, 
                           face_location: Optional[Tuple[int, int, int, int]] = None) -> Optional[dict]:
        """Get facial landmarks using eye detection"""
        if face_location is None:
            faces = self.detect_faces(frame)
            if not faces:
                return None
            face_location = faces[0]
        
        top, right, bottom, left = face_location
        face_roi = frame[top:bottom, left:right]
        gray_roi = cv2.cvtColor(face_roi, cv2.COLOR_BGR2GRAY)
        
        eyes = self.eye_cascade.detectMultiScale(gray_roi, 1.1, 3)
        
        if len(eyes) >= 2:
            eyes = sorted(eyes, key=lambda e: e[0])
            left_eye = eyes[0]
            right_eye = eyes[-1]
            
            def eye_to_landmarks(eye_rect, offset_x, offset_y):
                ex, ey, ew, eh = eye_rect
                cx = offset_x + ex + ew // 2
                cy = offset_y + ey + eh // 2
                r = ew // 3
                return [(cx - r, cy), (cx, cy - r), (cx + r, cy),
                        (cx, cy + r), (cx - r//2, cy - r//2), (cx + r//2, cy + r//2)]
            
            return {
                'left_eye': eye_to_landmarks(left_eye, left, top),
                'right_eye': eye_to_landmarks(right_eye, left, top)
            }
        
        # Fallback approximation
        face_h = bottom - top
        face_w = right - left
        eye_y = top + int(face_h * 0.35)
        left_eye_x = left + int(face_w * 0.3)
        right_eye_x = left + int(face_w * 0.7)
        r = int(face_w * 0.08)
        
        def make_eye_points(cx, cy):
            return [(cx - r, cy), (cx, cy - r), (cx + r, cy),
                    (cx, cy + r), (cx - r//2, cy - r//2), (cx + r//2, cy + r//2)]
        
        return {
            'left_eye': make_eye_points(left_eye_x, eye_y),
            'right_eye': make_eye_points(right_eye_x, eye_y)
        }
    
    def draw_face_box(self, frame: np.ndarray, 
                      face_location: Tuple[int, int, int, int],
                      name: str = "Unknown",
                      color: Tuple[int, int, int] = (0, 255, 0)) -> np.ndarray:
        """Draw a box around a detected face with label"""
        top, right, bottom, left = face_location
        
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.rectangle(frame, (left, bottom - 25), (right, bottom), color, cv2.FILLED)
        cv2.putText(frame, name, (left + 6, bottom - 6), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        return frame
    
    def crop_face(self, frame: np.ndarray, 
                  face_location: Tuple[int, int, int, int],
                  margin: float = 0.2) -> np.ndarray:
        """Crop face region from frame with optional margin"""
        top, right, bottom, left = face_location
        
        height = bottom - top
        width = right - left
        
        margin_h = int(height * margin)
        margin_w = int(width * margin)
        
        frame_h, frame_w = frame.shape[:2]
        new_top = max(0, top - margin_h)
        new_bottom = min(frame_h, bottom + margin_h)
        new_left = max(0, left - margin_w)
        new_right = min(frame_w, right + margin_w)
        
        return frame[new_top:new_bottom, new_left:new_right].copy()

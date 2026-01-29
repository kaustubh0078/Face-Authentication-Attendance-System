"""
Anti-Spoofing module for Face Authentication Attendance System
Implements liveness detection using blink detection (Eye Aspect Ratio)
"""
import cv2
import numpy as np
from scipy.spatial import distance as dist
from typing import Optional, Tuple, List, Dict
import time
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import EAR_THRESHOLD, BLINK_CONSEC_FRAMES, BLINK_TIMEOUT_SECONDS


class AntiSpoofing:
    """
    Anti-spoofing using Eye Aspect Ratio (EAR) blink detection
    
    The Eye Aspect Ratio is calculated as:
    EAR = (||p2-p6|| + ||p3-p5||) / (2 * ||p1-p4||)
    
    Where p1-p6 are the 6 landmark points around each eye.
    When the eye is open, EAR is relatively constant (~0.25-0.35).
    When the eye closes, EAR drops significantly (~0.1).
    """
    
    def __init__(self, 
                 ear_threshold: float = EAR_THRESHOLD,
                 consec_frames: int = BLINK_CONSEC_FRAMES,
                 timeout_seconds: float = BLINK_TIMEOUT_SECONDS):
        """
        Initialize anti-spoofing detector
        
        Args:
            ear_threshold: EAR below this value indicates closed eye
            consec_frames: Number of consecutive frames with low EAR to confirm blink
            timeout_seconds: Time window for user to complete blink challenge
        """
        self.ear_threshold = ear_threshold
        self.consec_frames = consec_frames
        self.timeout_seconds = timeout_seconds
        
        # Blink detection state
        self._blink_counter = 0
        self._total_blinks = 0
        self._challenge_start_time: Optional[float] = None
        self._challenge_active = False
        self._required_blinks = 1
        
    def calculate_ear(self, eye_points: List[Tuple[int, int]]) -> float:
        """
        Calculate the Eye Aspect Ratio for an eye
        
        Args:
            eye_points: List of 6 (x, y) coordinates for eye landmarks
                       Order: [left_corner, upper_left, upper_right, right_corner, lower_right, lower_left]
                       
        Returns:
            Eye Aspect Ratio value
        """
        if len(eye_points) != 6:
            return 0.0
        
        # Convert to numpy array for easier calculation
        eye = np.array(eye_points)
        
        # Compute vertical distances
        A = dist.euclidean(eye[1], eye[5])  # p2-p6
        B = dist.euclidean(eye[2], eye[4])  # p3-p5
        
        # Compute horizontal distance
        C = dist.euclidean(eye[0], eye[3])  # p1-p4
        
        # Calculate EAR
        if C == 0:
            return 0.0
        
        ear = (A + B) / (2.0 * C)
        return ear
    
    def get_average_ear(self, landmarks: dict) -> float:
        """
        Calculate average EAR for both eyes from face landmarks
        
        Args:
            landmarks: Dictionary with 'left_eye' and 'right_eye' keys
            
        Returns:
            Average EAR value for both eyes
        """
        if not landmarks or 'left_eye' not in landmarks or 'right_eye' not in landmarks:
            return 0.0
        
        left_ear = self.calculate_ear(landmarks['left_eye'])
        right_ear = self.calculate_ear(landmarks['right_eye'])
        
        return (left_ear + right_ear) / 2.0
    
    def start_challenge(self, required_blinks: int = 1):
        """
        Start a blink challenge
        
        Args:
            required_blinks: Number of blinks required to pass
        """
        self._challenge_start_time = time.time()
        self._challenge_active = True
        self._required_blinks = required_blinks
        self._total_blinks = 0
        self._blink_counter = 0
    
    def process_frame(self, landmarks: dict) -> Dict[str, any]:
        """
        Process a frame for blink detection
        
        Args:
            landmarks: Face landmarks dictionary
            
        Returns:
            Dictionary with:
                - ear: Current EAR value
                - is_blinking: Whether currently in blink
                - total_blinks: Total blinks detected
                - challenge_passed: Whether challenge is passed
                - challenge_active: Whether challenge is still active
                - time_remaining: Seconds remaining in challenge
        """
        result = {
            'ear': 0.0,
            'is_blinking': False,
            'total_blinks': self._total_blinks,
            'challenge_passed': False,
            'challenge_active': self._challenge_active,
            'time_remaining': 0.0
        }
        
        if not landmarks:
            return result
        
        # Calculate EAR
        ear = self.get_average_ear(landmarks)
        result['ear'] = ear
        
        # Check for blink
        if ear < self.ear_threshold:
            self._blink_counter += 1
        else:
            if self._blink_counter >= self.consec_frames:
                # Blink detected!
                self._total_blinks += 1
                result['is_blinking'] = True
            self._blink_counter = 0
        
        result['total_blinks'] = self._total_blinks
        
        # Check challenge status
        if self._challenge_active:
            elapsed = time.time() - self._challenge_start_time
            result['time_remaining'] = max(0, self.timeout_seconds - elapsed)
            
            if self._total_blinks >= self._required_blinks:
                result['challenge_passed'] = True
                self._challenge_active = False
            elif elapsed >= self.timeout_seconds:
                # Challenge timed out
                self._challenge_active = False
        
        return result
    
    def is_challenge_passed(self) -> bool:
        """Check if the current challenge has been passed"""
        return self._total_blinks >= self._required_blinks
    
    def is_challenge_active(self) -> bool:
        """Check if a challenge is currently active"""
        return self._challenge_active
    
    def reset(self):
        """Reset all detection state"""
        self._blink_counter = 0
        self._total_blinks = 0
        self._challenge_start_time = None
        self._challenge_active = False
    
    def get_status_message(self) -> str:
        """Get a user-friendly status message"""
        if not self._challenge_active:
            if self._total_blinks >= self._required_blinks:
                return "✅ Liveness verified!"
            return "⏸️ Challenge not started"
        
        elapsed = time.time() - self._challenge_start_time
        remaining = max(0, self.timeout_seconds - elapsed)
        
        if self._total_blinks < self._required_blinks:
            return f"👁️ Please blink! ({remaining:.1f}s remaining)"
        else:
            return "✅ Liveness verified!"
    
    def draw_eyes(self, frame: np.ndarray, landmarks: dict, 
                  color: Tuple[int, int, int] = (0, 255, 0)) -> np.ndarray:
        """
        Draw eye landmarks on frame for visualization
        
        Args:
            frame: BGR image
            landmarks: Face landmarks dictionary
            color: BGR color for drawing
            
        Returns:
            Frame with drawn eye landmarks
        """
        if not landmarks or 'left_eye' not in landmarks or 'right_eye' not in landmarks:
            return frame
        
        # Draw left eye
        left_eye = np.array(landmarks['left_eye'], dtype=np.int32)
        cv2.polylines(frame, [left_eye], True, color, 1)
        
        # Draw right eye
        right_eye = np.array(landmarks['right_eye'], dtype=np.int32)
        cv2.polylines(frame, [right_eye], True, color, 1)
        
        return frame


class TextureAnalyzer:
    """
    Optional: Texture-based anti-spoofing using Local Binary Patterns
    Helps detect printed photos which have different texture patterns
    """
    
    def __init__(self, threshold: float = 50.0):
        """
        Initialize texture analyzer
        
        Args:
            threshold: LBP variance threshold (lower = more likely to be fake)
        """
        self.threshold = threshold
    
    def analyze_texture(self, face_image: np.ndarray) -> Dict[str, any]:
        """
        Analyze face texture for signs of being a printed photo
        
        Args:
            face_image: Cropped face image (BGR)
            
        Returns:
            Dictionary with texture analysis results
        """
        # Convert to grayscale
        gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
        
        # Calculate Local Binary Pattern
        lbp = self._compute_lbp(gray)
        
        # Calculate variance (real faces have higher texture variance)
        variance = np.var(lbp)
        
        # Real faces typically have higher variance
        is_real = variance > self.threshold
        
        return {
            'texture_variance': float(variance),
            'is_real': is_real,
            'threshold': self.threshold,
            'confidence': min(100, (variance / self.threshold) * 50) if is_real else max(0, 50 - (self.threshold - variance))
        }
    
    def _compute_lbp(self, gray: np.ndarray, radius: int = 1, n_points: int = 8) -> np.ndarray:
        """
        Compute Local Binary Pattern
        
        Simple implementation for detecting texture differences
        """
        rows, cols = gray.shape
        lbp = np.zeros_like(gray)
        
        for i in range(radius, rows - radius):
            for j in range(radius, cols - radius):
                center = gray[i, j]
                code = 0
                for k in range(n_points):
                    x = int(round(i + radius * np.cos(2 * np.pi * k / n_points)))
                    y = int(round(j - radius * np.sin(2 * np.pi * k / n_points)))
                    if gray[x, y] >= center:
                        code |= (1 << k)
                lbp[i, j] = code
        
        return lbp

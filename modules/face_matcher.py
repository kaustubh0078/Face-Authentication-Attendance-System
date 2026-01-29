"""
Face Matching module for Face Authentication Attendance System
Handles face recognition and identity matching using cosine similarity
"""
import numpy as np
from typing import Optional, Tuple, List, Dict, Any
from scipy.spatial.distance import cosine
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import RECOGNITION_THRESHOLD


class FaceMatcher:
    """Handles face matching and identity verification"""
    
    def __init__(self, threshold: float = RECOGNITION_THRESHOLD):
        """
        Initialize face matcher
        
        Args:
            threshold: Maximum distance for a positive match (lower = stricter)
                      For cosine distance on histogram features: 0.3-0.5 recommended
        """
        self.threshold = threshold
        self._known_encodings: List[np.ndarray] = []
        self._known_user_ids: List[int] = []
        self._known_names: List[str] = []
    
    def load_known_faces(self, users: List[Dict[str, Any]]):
        """
        Load known face encodings from user records
        
        Args:
            users: List of user dictionaries with 'id', 'name', and 'face_encoding' keys
        """
        self._known_encodings = []
        self._known_user_ids = []
        self._known_names = []
        
        for user in users:
            if user['face_encoding'] is not None:
                self._known_encodings.append(user['face_encoding'])
                self._known_user_ids.append(user['id'])
                self._known_names.append(user['name'])
    
    def _cosine_distance(self, encoding1: np.ndarray, encoding2: np.ndarray) -> float:
        """Calculate cosine distance between two encodings"""
        try:
            # Ensure same length (in case of different encoding methods)
            min_len = min(len(encoding1), len(encoding2))
            enc1 = encoding1[:min_len]
            enc2 = encoding2[:min_len]
            return cosine(enc1, enc2)
        except Exception:
            return 1.0  # Max distance on error
    
    def _euclidean_distance(self, encoding1: np.ndarray, encoding2: np.ndarray) -> float:
        """Calculate normalized euclidean distance"""
        min_len = min(len(encoding1), len(encoding2))
        enc1 = encoding1[:min_len]
        enc2 = encoding2[:min_len]
        
        # Normalize
        enc1 = enc1 / (np.linalg.norm(enc1) + 1e-10)
        enc2 = enc2 / (np.linalg.norm(enc2) + 1e-10)
        
        return np.linalg.norm(enc1 - enc2)
    
    def match_face(self, encoding: np.ndarray) -> Tuple[Optional[int], Optional[str], float]:
        """
        Match a face encoding against known faces
        
        Args:
            encoding: Face embedding to match
            
        Returns:
            Tuple of (user_id, name, distance) if match found, else (None, None, min_distance)
        """
        if not self._known_encodings:
            return None, None, float('inf')
        
        # Calculate distances to all known faces
        distances = []
        for known_enc in self._known_encodings:
            dist = self._cosine_distance(encoding, known_enc)
            distances.append(dist)
        
        # Find the best match
        min_distance_idx = np.argmin(distances)
        min_distance = distances[min_distance_idx]
        
        # Check if it's within threshold
        if min_distance <= self.threshold:
            return (
                self._known_user_ids[min_distance_idx],
                self._known_names[min_distance_idx],
                min_distance
            )
        
        return None, None, min_distance
    
    def get_match_confidence(self, distance: float) -> float:
        """
        Convert distance to confidence percentage
        
        Args:
            distance: Cosine distance (0.0 = identical, 2.0 = opposite)
            
        Returns:
            Confidence percentage (0-100)
        """
        if distance <= 0:
            return 100.0
        
        # Convert distance to similarity
        similarity = 1 - min(distance, 1.0)
        
        # Scale to percentage (considering threshold)
        if distance <= self.threshold:
            # Good match: 50-100%
            confidence = 50 + (similarity * 50)
        else:
            # Poor match: 0-50%
            confidence = similarity * 50
        
        return max(0, min(100, confidence))
    
    def find_all_matches(self, encoding: np.ndarray, 
                         top_k: int = 3) -> List[Tuple[int, str, float, float]]:
        """
        Find top K matches for a face encoding
        
        Args:
            encoding: Face embedding
            top_k: Number of top matches to return
            
        Returns:
            List of (user_id, name, distance, confidence) tuples, sorted by distance
        """
        if not self._known_encodings:
            return []
        
        distances = []
        for known_enc in self._known_encodings:
            dist = self._cosine_distance(encoding, known_enc)
            distances.append(dist)
        
        # Get indices sorted by distance
        sorted_indices = np.argsort(distances)[:top_k]
        
        results = []
        for idx in sorted_indices:
            distance = distances[idx]
            confidence = self.get_match_confidence(distance)
            results.append((
                self._known_user_ids[idx],
                self._known_names[idx],
                distance,
                confidence
            ))
        
        return results
    
    def verify_face(self, encoding1: np.ndarray, encoding2: np.ndarray) -> Tuple[bool, float]:
        """
        Verify if two face encodings belong to the same person
        """
        distance = self._cosine_distance(encoding1, encoding2)
        is_same = distance <= self.threshold
        return is_same, distance
    
    def compare_faces(self, known_encoding: np.ndarray, 
                      unknown_encoding: np.ndarray) -> Dict[str, Any]:
        """
        Compare two faces and return detailed results
        """
        distance = self._cosine_distance(known_encoding, unknown_encoding)
        is_match = distance <= self.threshold
        confidence = self.get_match_confidence(distance)
        
        return {
            'is_match': is_match,
            'distance': float(distance),
            'confidence': confidence,
            'threshold': self.threshold
        }
    
    @property
    def num_known_faces(self) -> int:
        """Return the number of known faces loaded"""
        return len(self._known_encodings)

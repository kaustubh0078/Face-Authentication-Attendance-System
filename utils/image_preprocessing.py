"""
Image preprocessing utilities for Face Authentication Attendance System
Handles lighting normalization and image enhancement
"""
import cv2
import numpy as np
from typing import Tuple
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ENABLE_LIGHTING_NORMALIZATION, CLAHE_CLIP_LIMIT, CLAHE_TILE_SIZE


def normalize_lighting(frame: np.ndarray, 
                       clip_limit: float = CLAHE_CLIP_LIMIT,
                       tile_size: Tuple[int, int] = CLAHE_TILE_SIZE) -> np.ndarray:
    """
    Normalize lighting using CLAHE (Contrast Limited Adaptive Histogram Equalization)
    
    This helps handle varying lighting conditions by locally enhancing contrast
    
    Args:
        frame: BGR image
        clip_limit: Threshold for contrast limiting
        tile_size: Size of grid for histogram equalization
        
    Returns:
        Lighting-normalized BGR image
    """
    # Convert to LAB color space
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    
    # Split channels
    l, a, b = cv2.split(lab)
    
    # Apply CLAHE to L channel
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_size)
    l_clahe = clahe.apply(l)
    
    # Merge channels
    lab_clahe = cv2.merge([l_clahe, a, b])
    
    # Convert back to BGR
    result = cv2.cvtColor(lab_clahe, cv2.COLOR_LAB2BGR)
    
    return result


def adjust_gamma(frame: np.ndarray, gamma: float = 1.0) -> np.ndarray:
    """
    Adjust image brightness using gamma correction
    
    Args:
        frame: BGR image
        gamma: Gamma value (< 1 = brighter, > 1 = darker)
        
    Returns:
        Gamma-corrected image
    """
    inv_gamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** inv_gamma) * 255
                      for i in np.arange(0, 256)]).astype("uint8")
    
    return cv2.LUT(frame, table)


def auto_adjust_brightness(frame: np.ndarray, target_brightness: float = 127) -> np.ndarray:
    """
    Automatically adjust brightness to target level
    
    Args:
        frame: BGR image
        target_brightness: Target average brightness (0-255)
        
    Returns:
        Brightness-adjusted image
    """
    # Convert to grayscale and calculate mean brightness
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    current_brightness = np.mean(gray)
    
    if current_brightness == 0:
        return frame
    
    # Calculate gamma for correction
    gamma = np.log(target_brightness / 255.0) / np.log(current_brightness / 255.0)
    gamma = np.clip(gamma, 0.5, 2.0)  # Limit extreme adjustments
    
    return adjust_gamma(frame, gamma)


def reduce_noise(frame: np.ndarray, strength: int = 10) -> np.ndarray:
    """
    Reduce noise while preserving edges
    
    Args:
        frame: BGR image
        strength: Denoising strength (higher = more smoothing)
        
    Returns:
        Denoised image
    """
    return cv2.fastNlMeansDenoisingColored(frame, None, strength, strength, 7, 21)


def sharpen_image(frame: np.ndarray, strength: float = 1.0) -> np.ndarray:
    """
    Sharpen image to enhance facial features
    
    Args:
        frame: BGR image
        strength: Sharpening strength
        
    Returns:
        Sharpened image
    """
    kernel = np.array([
        [0, -1, 0],
        [-1, 5 + strength, -1],
        [0, -1, 0]
    ])
    
    return cv2.filter2D(frame, -1, kernel)


def preprocess_frame(frame: np.ndarray, 
                     normalize: bool = ENABLE_LIGHTING_NORMALIZATION,
                     denoise: bool = False,
                     sharpen: bool = False) -> np.ndarray:
    """
    Apply full preprocessing pipeline to a frame
    
    Args:
        frame: BGR image
        normalize: Apply lighting normalization
        denoise: Apply noise reduction
        sharpen: Apply sharpening
        
    Returns:
        Preprocessed image
    """
    result = frame.copy()
    
    if normalize:
        result = normalize_lighting(result)
    
    if denoise:
        result = reduce_noise(result, strength=5)
    
    if sharpen:
        result = sharpen_image(result, strength=0.5)
    
    return result


def resize_for_display(frame: np.ndarray, max_width: int = 640) -> np.ndarray:
    """
    Resize frame for display while maintaining aspect ratio
    
    Args:
        frame: BGR image
        max_width: Maximum width for display
        
    Returns:
        Resized image
    """
    height, width = frame.shape[:2]
    
    if width <= max_width:
        return frame
    
    scale = max_width / width
    new_height = int(height * scale)
    
    return cv2.resize(frame, (max_width, new_height))


def get_image_quality_score(frame: np.ndarray) -> dict:
    """
    Assess image quality for face recognition
    
    Args:
        frame: BGR image
        
    Returns:
        Dictionary with quality metrics
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Brightness
    brightness = np.mean(gray)
    brightness_ok = 50 < brightness < 200
    
    # Contrast (standard deviation)
    contrast = np.std(gray)
    contrast_ok = contrast > 30
    
    # Sharpness (Laplacian variance)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    sharpness_ok = laplacian_var > 100
    
    # Overall assessment
    is_good = brightness_ok and contrast_ok and sharpness_ok
    
    return {
        'brightness': float(brightness),
        'brightness_ok': brightness_ok,
        'contrast': float(contrast),
        'contrast_ok': contrast_ok,
        'sharpness': float(laplacian_var),
        'sharpness_ok': sharpness_ok,
        'overall_ok': is_good
    }

"""
Helper utilities for Face Authentication Attendance System
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple
import os


def format_timestamp(timestamp: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format a timestamp string for display
    
    Args:
        timestamp: Timestamp string from database
        format_str: Output format string
        
    Returns:
        Formatted timestamp string
    """
    if not timestamp:
        return "N/A"
    
    try:
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime(format_str)
    except (ValueError, TypeError):
        return str(timestamp)


def format_time_only(timestamp: str) -> str:
    """Format timestamp to show only time"""
    return format_timestamp(timestamp, "%H:%M:%S")


def format_date_only(timestamp: str) -> str:
    """Format timestamp to show only date"""
    return format_timestamp(timestamp, "%Y-%m-%d")


def calculate_work_hours(punch_in: Optional[str], punch_out: Optional[str]) -> Optional[str]:
    """
    Calculate work hours between punch-in and punch-out
    
    Args:
        punch_in: Punch-in timestamp
        punch_out: Punch-out timestamp
        
    Returns:
        Formatted duration string (e.g., "8h 30m") or None
    """
    if not punch_in or not punch_out:
        return None
    
    try:
        dt_in = datetime.fromisoformat(punch_in)
        dt_out = datetime.fromisoformat(punch_out)
        
        duration = dt_out - dt_in
        
        if duration.total_seconds() < 0:
            return "Invalid"
        
        hours, remainder = divmod(int(duration.total_seconds()), 3600)
        minutes = remainder // 60
        
        return f"{hours}h {minutes}m"
    except (ValueError, TypeError):
        return None


def get_greeting() -> str:
    """Get time-appropriate greeting"""
    hour = datetime.now().hour
    
    if 5 <= hour < 12:
        return "Good Morning"
    elif 12 <= hour < 17:
        return "Good Afternoon"
    elif 17 <= hour < 21:
        return "Good Evening"
    else:
        return "Hello"


def ensure_dir_exists(path: str):
    """Ensure a directory exists, create if not"""
    os.makedirs(path, exist_ok=True)


def get_today_str() -> str:
    """Get today's date as string"""
    return datetime.now().strftime("%Y-%m-%d")


def get_current_time_str() -> str:
    """Get current time as string"""
    return datetime.now().strftime("%H:%M:%S")


def is_valid_employee_id(employee_id: str) -> Tuple[bool, str]:
    """
    Validate employee ID format
    
    Args:
        employee_id: Employee ID to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not employee_id:
        return False, "Employee ID is required"
    
    if len(employee_id) < 2:
        return False, "Employee ID must be at least 2 characters"
    
    if len(employee_id) > 20:
        return False, "Employee ID must not exceed 20 characters"
    
    # Allow alphanumeric and some special characters
    allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")
    if not all(c in allowed_chars for c in employee_id):
        return False, "Employee ID can only contain letters, numbers, hyphens, and underscores"
    
    return True, ""


def is_valid_name(name: str) -> Tuple[bool, str]:
    """
    Validate user name
    
    Args:
        name: Name to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name:
        return False, "Name is required"
    
    if len(name) < 2:
        return False, "Name must be at least 2 characters"
    
    if len(name) > 100:
        return False, "Name must not exceed 100 characters"
    
    return True, ""


def get_punch_status_emoji(punch_type: Optional[str]) -> str:
    """Get emoji for punch status"""
    if punch_type == "IN":
        return "🟢"
    elif punch_type == "OUT":
        return "🔴"
    return "⚪"


def distance_to_percentage(distance: float, threshold: float = 0.6) -> float:
    """
    Convert face distance to match percentage
    
    Args:
        distance: Face distance value
        threshold: Recognition threshold
        
    Returns:
        Match percentage (0-100)
    """
    if distance >= threshold:
        return max(0, (1 - distance) * 100)
    
    # Scale from 0-threshold to 50-100%
    return 50 + (1 - distance / threshold) * 50

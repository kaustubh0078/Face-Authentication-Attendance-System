"""
Database module for Face Authentication Attendance System
Handles user registration and attendance logging using SQLite
"""
import sqlite3
import pickle
import os
from datetime import datetime, date
from typing import Optional, List, Tuple, Dict, Any
import numpy as np

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATABASE_PATH, FACE_IMAGES_DIR


class DatabaseManager:
    """Manages SQLite database operations for users and attendance"""
    
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        self._init_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Create and return a database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_database(self):
        """Initialize database tables if they don't exist"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                employee_id TEXT UNIQUE NOT NULL,
                face_encoding BLOB NOT NULL,
                image_path TEXT,
                registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Attendance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                punch_type TEXT NOT NULL CHECK(punch_type IN ('IN', 'OUT')),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def register_user(self, name: str, employee_id: str, 
                      face_encoding: np.ndarray, image_path: Optional[str] = None) -> int:
        """
        Register a new user with their face encoding
        
        Args:
            name: User's full name
            employee_id: Unique employee identifier
            face_encoding: 128-dimensional face embedding
            image_path: Optional path to stored face image
            
        Returns:
            User ID of the registered user
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Serialize the numpy array
        encoding_blob = pickle.dumps(face_encoding)
        
        try:
            cursor.execute('''
                INSERT INTO users (name, employee_id, face_encoding, image_path)
                VALUES (?, ?, ?, ?)
            ''', (name, employee_id, encoding_blob, image_path))
            
            conn.commit()
            user_id = cursor.lastrowid
        except sqlite3.IntegrityError:
            conn.close()
            raise ValueError(f"Employee ID '{employee_id}' already exists")
        
        conn.close()
        return user_id
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user details by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._row_to_user_dict(row)
        return None
    
    def get_user_by_employee_id(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """Get user details by employee ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE employee_id = ?', (employee_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return self._row_to_user_dict(row)
        return None
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """Get all registered users with their face encodings"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users ORDER BY name')
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_user_dict(row) for row in rows]
    
    def _row_to_user_dict(self, row: sqlite3.Row) -> Dict[str, Any]:
        """Convert a database row to a user dictionary"""
        return {
            'id': row['id'],
            'name': row['name'],
            'employee_id': row['employee_id'],
            'face_encoding': pickle.loads(row['face_encoding']),
            'image_path': row['image_path'],
            'registration_date': row['registration_date']
        }
    
    def delete_user(self, user_id: int) -> bool:
        """Delete a user and their attendance records"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Delete attendance records first
        cursor.execute('DELETE FROM attendance WHERE user_id = ?', (user_id,))
        
        # Delete user
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        return deleted
    
    def log_attendance(self, user_id: int, punch_type: str) -> int:
        """
        Log a punch-in or punch-out event
        
        Args:
            user_id: ID of the user
            punch_type: 'IN' or 'OUT'
            
        Returns:
            Attendance record ID
        """
        if punch_type not in ('IN', 'OUT'):
            raise ValueError("punch_type must be 'IN' or 'OUT'")
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Use explicit local timestamp instead of SQLite's CURRENT_TIMESTAMP (which is UTC)
        local_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute('''
            INSERT INTO attendance (user_id, punch_type, timestamp)
            VALUES (?, ?, ?)
        ''', (user_id, punch_type, local_timestamp))
        
        conn.commit()
        record_id = cursor.lastrowid
        conn.close()
        
        return record_id
    
    def get_last_punch(self, user_id: int, date_filter: Optional[date] = None) -> Optional[str]:
        """
        Get the last punch type for a user (to determine if next should be IN or OUT)
        
        Args:
            user_id: ID of the user
            date_filter: Optional date to filter by (defaults to today)
            
        Returns:
            'IN', 'OUT', or None if no punches today
        """
        if date_filter is None:
            date_filter = date.today()
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT punch_type FROM attendance 
            WHERE user_id = ? AND date(timestamp) = ?
            ORDER BY timestamp DESC LIMIT 1
        ''', (user_id, date_filter.isoformat()))
        
        row = cursor.fetchone()
        conn.close()
        
        return row['punch_type'] if row else None
    
    def get_attendance_history(self, user_id: Optional[int] = None, 
                                date_from: Optional[date] = None,
                                date_to: Optional[date] = None) -> List[Dict[str, Any]]:
        """
        Get attendance history with optional filters
        
        Args:
            user_id: Filter by specific user (None for all users)
            date_from: Start date filter
            date_to: End date filter
            
        Returns:
            List of attendance records with user info
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = '''
            SELECT a.*, u.name, u.employee_id 
            FROM attendance a
            JOIN users u ON a.user_id = u.id
            WHERE 1=1
        '''
        params = []
        
        if user_id:
            query += ' AND a.user_id = ?'
            params.append(user_id)
        
        if date_from:
            query += ' AND date(a.timestamp) >= ?'
            params.append(date_from.isoformat())
        
        if date_to:
            query += ' AND date(a.timestamp) <= ?'
            params.append(date_to.isoformat())
        
        query += ' ORDER BY a.timestamp DESC'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_today_attendance_summary(self) -> List[Dict[str, Any]]:
        """Get today's attendance summary for all users"""
        today = date.today()
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.id, u.name, u.employee_id,
                   MIN(CASE WHEN a.punch_type = 'IN' THEN a.timestamp END) as first_in,
                   MAX(CASE WHEN a.punch_type = 'OUT' THEN a.timestamp END) as last_out,
                   COUNT(CASE WHEN a.punch_type = 'IN' THEN 1 END) as punch_in_count,
                   COUNT(CASE WHEN a.punch_type = 'OUT' THEN 1 END) as punch_out_count
            FROM users u
            LEFT JOIN attendance a ON u.id = a.user_id AND date(a.timestamp) = ?
            GROUP BY u.id
            ORDER BY u.name
        ''', (today.isoformat(),))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]

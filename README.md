# Face Authentication Attendance System

A modern face authentication system with **React frontend** and **Flask API backend** for attendance management. Features real-time face recognition, attendance tracking, and a beautiful dark-themed dashboard.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![React](https://img.shields.io/badge/React-19.0+-61DAFB.svg)
![Flask](https://img.shields.io/badge/Flask-3.0+-black.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## 🌟 Features

- **👤 Face Registration** - Register users with webcam capture and face encoding
- **🔍 Face Recognition** - Real-time face identification with confidence scoring
- **✅ Attendance Tracking** - Separate Punch IN/OUT with automatic logging
- **📊 Modern Dashboard** - Beautiful dark-themed UI with live attendance status
- **📜 History View** - Detailed attendance records with date filtering
- **💡 Lighting Adaptation** - CLAHE preprocessing for varying conditions
- **⚡ Fast & Responsive** - React frontend with Flask API backend
- **🕒 Local Time Support** - Correctly records your timezone

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Node.js 18 or higher
- Webcam

### Installation

1. **Navigate to the project directory:**
   ```bash
   cd "Face Authentication Attendance System"
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Node.js dependencies:**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

### Running the Application

**Option 1: One-Click Startup (Recommended)**

Simply **double-click `START.bat`** in the project folder. It will:
- Start the Flask API server
- Start the React development server
- Open your browser automatically to http://localhost:3000

**Option 2: Manual Startup**

Open two terminal windows:

**Terminal 1 - Flask API:**
```bash
python api.py
```

**Terminal 2 - React Frontend:**
```bash
cd frontend
npm run dev
```

Then open your browser to http://localhost:3000

## 📖 Usage Guide

### 1. Register Users

1. Click **Register User** in the sidebar
2. Enter the user's name and employee ID
3. Click **Capture Photo** to take a picture
4. Click **Register User**
5. User is now enrolled in the system

### 2. Mark Attendance

1. Click **Mark Attendance** in the sidebar
2. Look at the camera
3. Click **Recognize Face** - system will identify you
4. Click **Punch IN** or **Punch OUT** as needed
5. Dashboard updates automatically

### 3. View Records

- **Dashboard** - Today's overview with live attendance status
- **Attendance History** - Detailed records with date filters
- **Settings** - Manage registered users

## 🏗️ Architecture

```
┌─────────────────┐      HTTP/JSON      ┌──────────────────┐
│  React Frontend │ ◄─────────────────► │   Flask API      │
│  (Port 3000)    │                     │   (Port 5000)    │
└─────────────────┘                     └──────────────────┘
                                                 │
                                                 ▼
                                        ┌──────────────────┐
                                        │  SQLite Database │
                                        │  Face Encodings  │
                                        └──────────────────┘
```

### Technology Stack

**Frontend:**
- React 19 with Vite
- TailwindCSS for styling
- react-webcam for camera access
- Lucide React icons

**Backend:**
- Flask 3.0 REST API
- OpenCV for face detection
- Custom histogram-based face encoding
- SQLite for data persistence

## 📁 Project Structure

```
Face Authentication Attendance System/
├── START.bat              # One-click startup script
├── api.py                 # Flask REST API
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── README.md              # This file
│
├── frontend/              # React application
│   ├── package.json       # Node dependencies
│   ├── vite.config.js     # Vite configuration
│   ├── index.html         # HTML entry point
│   └── src/
│       ├── App.jsx        # Main React component
│       ├── main.jsx       # React entry point
│       └── index.css      # Tailwind CSS
│
├── modules/
│   ├── database.py        # SQLite operations
│   ├── face_detector.py   # Face detection & encoding
│   ├── face_matcher.py    # Face matching logic
│   └── anti_spoof.py      # Liveness detection
│
├── utils/
│   ├── image_preprocessing.py  # Lighting normalization
│   └── helpers.py              # Utility functions
│
├── data/
│   ├── faces.db          # SQLite database (auto-created)
│   └── face_images/      # Stored face images
│
└── docs/
    └── DOCUMENTATION.md  # Technical documentation
```

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/users` | GET | Get all registered users |
| `/api/users` | POST | Register new user |
| `/api/users/<id>` | DELETE | Delete user |
| `/api/recognize` | POST | Recognize face from image |
| `/api/punch` | POST | Log attendance (IN/OUT) |
| `/api/attendance` | GET | Get attendance history |
| `/api/attendance/today` | GET | Get today's summary |
| `/api/stats` | GET | Get dashboard statistics |

## ⚙️ Configuration

Edit `config.py` to customize:

| Setting | Default | Description |
|---------|---------|-------------|
| `RECOGNITION_THRESHOLD` | 0.25 | Lower = stricter matching |
| `FACE_DETECTION_MODEL` | "hog" | "hog" (fast) or "cnn" (accurate) |
| `DATABASE_PATH` | "data/faces.db" | SQLite database location |

## 🧠 Technical Details

See [DOCUMENTATION.md](docs/DOCUMENTATION.md) for:
- Face encoding algorithm explanation
- Recognition accuracy expectations
- Known limitations and failure cases
- Lighting handling with CLAHE

## 🛠️ Development

**Frontend Development:**
```bash
cd frontend
npm run dev     # Development server with hot reload
npm run build   # Production build
```

**Backend Development:**
```bash
python api.py   # Flask runs in debug mode
```

## 📝 Notes

- **First Time Setup:** After installation, register at least one user before marking attendance
- **Camera Permissions:** Browser will request camera access - click "Allow"
- **Timezone:** System uses your local timezone for timestamps
- **Re-registration:** Delete old users in Settings before re-registering with new photos
- **Port Conflicts:** If ports 3000 or 5000 are in use, you'll need to change them in the code

## 📄 License

This project is for educational purposes.

## 🤝 Contributing

Feel free to fork, modify, and use this project for your needs!

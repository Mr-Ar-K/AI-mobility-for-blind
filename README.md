# AI Mobility for the Blind

**AI-powered object detection system with voice control, designed to assist visually impaired users.**

This application combines a powerful FastAPI backend with YOLO object detection models and a fully voice-controlled frontend to provide real-time audio feedback about detected objects in uploaded videos or images.

---

## 🌟 Features

### Core Functionality
- **Multi-Model Object Detection**: Uses three specialized YOLO models:
  - General object detection (YOLOv8m) - cars, people, etc.
  - Traffic lights detection
  - Zebra crossing detection
- **Video & Image Processing**: Upload videos or images for instant object detection
- **Text-to-Speech Audio Feedback**: Automatically generates audio descriptions of detected objects
- **Detection History**: Saves all detections with video/image and audio files organized by user and timestamp
- **User Authentication**: Secure user registration and login system

### Voice Control (Hands-Free Operation)
- **Complete Voice Navigation**: Navigate the entire app using voice commands
- **Voice Form Input**: Fill login, registration, and feedback forms by voice
- **Audio Playback Control**: Play, pause, and control detection audio via voice
- **Real-time Feedback**: Voice confirmation for all actions

### Backend Integration
- **Automatic Backend Fallback**: Connects to DevTunnel (HTTPS) or falls back to local servers
- **RESTful API**: Well-structured endpoints for users, detection, and history
- **Organized File Storage**: User files stored by username and timestamp
- **CORS Enabled**: Ready for cross-origin frontend requests

---

## 📋 Prerequisites

- **Python 3.10+**
- **PostgreSQL** (running locally with a database named `ai_mobility_db`)
- Optional: **Anaconda/Miniconda** (for Conda environments)
- A modern web browser with **Web Speech API support** (Chrome recommended for voice control)

---

## 🚀 Quick Start

### 1) Create and Activate Virtual Environment

**Option A — Conda (Recommended)**
```powershell
conda create -p .\venv python=3.10 -y
conda activate .\venv
```

**Option B — Python venv**
```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2) Install Dependencies

```powershell
pip install -r requirements.txt
```

### 3) Configure Backend Settings

Create or edit `backend/.env` file:

```env
# Database connection
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost/ai_mobility_db

# Model paths (three models for multi-detection)
MODEL_PATH_YOLO=models/yolov8m.pt
MODEL_PATH_TRAFFIC_LIGHTS=models/traffic lights.pt
MODEL_PATH_ZEBRA_CROSSING=models/zebra crossing.pt

# Backend URLs (for frontend configuration)
Backend_PORT=https://cjcf4dl2-8000.inc1.devtunnels.ms
Backend_PORT_FALLBACK=http://0.0.0.0:8000

# Storage directories
HISTORY_STORAGE_DIR=storage/history
TEMP_UPLOAD_DIR=tmp/
```

**Important**: Ensure all three YOLO model files exist in the `backend/models/` directory.

### 4) Start the Backend Server (FastAPI)

```powershell
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

If `uvicorn` is not recognized:
```powershell
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

✅ Backend running at: http://localhost:8000  
📖 API documentation: http://localhost:8000/docs

### 5) Start the Frontend Server

Open a **NEW terminal** (keep backend running), activate the environment again:

```powershell
cd frontend
python -m http.server 5500
```

✅ Frontend running at: http://localhost:5500

---

## 🎮 How to Use

### First Time Setup
1. Open http://localhost:5500 in your browser
2. Click **"Register"** or say **"register"** (voice control starts automatically)
3. Fill in your details:
   - By typing **OR**
   - By voice: _"first name is John"_, _"email is john at example dot com"_, _"password is mypassword"_, _"create account"_
4. Login with your credentials

### Uploading Media for Detection
1. Navigate to **Upload** page (click or say _"go to upload"_)
2. Select a video or image file
3. Say **"upload video"** or click the upload button
4. Wait for detection results
5. Listen to the audio summary or read the text results
6. Control audio playback: _"play audio"_, _"pause"_

### Viewing Detection History
1. Go to **Detections** page (say _"go to detections"_)
2. View all your past detections with timestamps
3. Play any audio: _"play first audio"_, _"play audio number 2"_

### Voice Commands Reference

**Navigation**
- _"go to home/upload/detections/about/profile/settings/feedback"_
- _"logout"_

**Login Page**
- _"email is [your email]"_
- _"password is [your password]"_
- _"login"_

**Registration Page**
- _"first name is [name]"_
- _"email is [email]"_
- _"password is [password]"_
- _"create account"_

**Upload Page**
- _"upload video"_ (after selecting file)

**Audio Control**
- _"play audio"_ / _"play the summary"_
- _"pause"_
- _"play first/second/third audio"_
- _"play audio number [X]"_

**Profile Page**
- _"first name is [new name]"_
- _"update profile"_

**Feedback Page**
- _"feedback is [your feedback]"_
- _"submit feedback"_

**Settings Page**
- _"set language english"_
- _"save settings"_

---

## 📁 Project Structure

```
AI-mobility-for-blind/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application entry point
│   │   ├── core/
│   │   │   └── config.py        # Configuration settings
│   │   ├── db/
│   │   │   ├── database.py      # Database connection
│   │   │   ├── models.py        # SQLAlchemy models
│   │   │   └── schemas.py       # Pydantic schemas
│   │   ├── routers/
│   │   │   ├── users.py         # User authentication endpoints
│   │   │   ├── detection.py     # Video/image detection endpoints
│   │   │   └── history.py       # Detection history endpoints
│   │   └── services/
│   │       ├── video_processor.py
│   │       └── audio_generator.py
│   ├── models/                  # YOLO model files (.pt)
│   ├── storage/history/         # User detection files (organized by user/date/time)
│   └── tmp/                     # Temporary upload directory
├── frontend/
│   ├── index.html               # Landing page
│   ├── login.html               # Login page
│   ├── register.html            # Registration page
│   ├── home.html                # Home dashboard
│   ├── upload.html              # Upload media page
│   ├── detections.html          # Detection history page
│   ├── profile.html             # User profile page
│   ├── about.html               # About page
│   ├── feedback.html            # Feedback page
│   ├── settings.html            # Settings page
│   ├── css/
│   │   └── style.css            # Complete stylesheet (Object-Detecto theme)
│   └── js/
│       ├── api.js               # API client with automatic backend fallback
│       ├── auth.js              # Authentication guard
│       ├── voice.js             # Voice control system (Web Speech API)
│       ├── login.js             # Login page logic
│       ├── register.js          # Registration page logic
│       ├── home.js              # Home page and navbar logic
│       ├── upload.js            # Upload and detection logic
│       ├── detections.js        # History display logic
│       └── profile.js           # Profile management logic
└── requirements.txt             # Python dependencies
```

---

## 🔧 API Endpoints

### Users
- `POST /users/signup` - Register new user
- `POST /users/login` - Login user
- `GET /users/{user_id}` - Get user details
- `PUT /users/{user_id}` - Update user profile

### Detection
- `POST /detect/{user_id}/with-audio` - Process video/image and return results with audio
- `POST /detect/image/{user_id}/with-audio` - Process image specifically
- `POST /detect/generate-audio` - Generate audio from text list

### History
- `GET /history/{user_id}` - Get all detections for user
- `GET /history/by-username/{username}` - Get history by username
- `GET /history/audio/{detection_id}` - Stream audio file
- `GET /history/video/{detection_id}` - Stream video file
- `GET /history/image/{detection_id}` - Stream image file
- `DELETE /history/{detection_id}` - Delete detection and files

---

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM for database operations
- **PostgreSQL** - Relational database
- **Ultralytics YOLO** - Object detection models
- **gTTS** - Text-to-speech audio generation
- **Pydantic** - Data validation

### Frontend
- **HTML5/CSS3** - Modern web standards
- **Vanilla JavaScript** - No framework dependencies
- **Web Speech API** - Voice recognition and synthesis
- **Fetch API** - HTTP requests with automatic fallback

---

## 🎨 Design

The frontend uses a custom theme inspired by the Object-Detecto project, featuring:
- Clean, accessible design
- Responsive layout (mobile-friendly)
- Consistent color scheme using CSS custom properties
- Card-based UI for detection history
- Integrated audio players

---

## 🔊 Voice Control Details

The voice control system uses the **Web Speech API** and provides:
- **Continuous listening** - Always ready for commands
- **Voice feedback** - Confirms actions audibly
- **Context-aware commands** - Different commands per page
- **Fallback gracefully** - Works without voice if not supported

Voice control activates automatically on page load and announces _"Voice control activated"_.

---

## 🐛 Troubleshooting

### Backend Issues

**"uvicorn not recognized"**
- Ensure virtual environment is activated
- Run: `python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- Or install: `pip install uvicorn[standard]`

**PostgreSQL connection errors**
- Verify PostgreSQL is running: `Get-Service postgresql*`
- Check database exists: `psql -U postgres -c "\l"`
- Confirm credentials in `backend/.env`

**Model loading errors**
- Ensure all three `.pt` files exist in `backend/models/`
- Check file paths in `.env` match actual locations

### Frontend Issues

**Voice control not working**
- Use Chrome or Edge (best Web Speech API support)
- Allow microphone permissions when prompted
- Check browser console for errors

**"Not logged in" errors**
- Clear browser localStorage: `localStorage.clear()` in console
- Register and login again

**Audio not playing**
- Check backend URL in `frontend/js/api.js`
- Verify CORS is enabled in backend
- Ensure detection has completed successfully

**Backend connection fails**
- Primary DevTunnel may be down - system auto-falls back to localhost
- Ensure backend is running on port 8000
- Check `API_BASES` array in `frontend/js/api.js`

---

## 🛑 Stopping the Application

1. Press **Ctrl+C** in each terminal to stop servers
2. Deactivate virtual environment:
   - Conda: `conda deactivate`
   - Python venv: `deactivate`

---

## 📝 Notes

- **Security**: Current implementation uses plain password storage. For production, implement proper password hashing (bcrypt, argon2).
- **Authentication**: Uses localStorage for session management. Consider JWT tokens for production.
- **Voice Privacy**: Voice recognition happens in the browser; no voice data is sent to servers.
- **File Storage**: Detection files are organized by username and timestamp in `storage/history/`.
- **Model Performance**: Processing time depends on video length and hardware capabilities.


---

## 📄 License

See LICENSE file for details.

---

## 🙏 Acknowledgments

- **Ultralytics YOLOv8** - Object detection models
- **FastAPI** - Backend framework
- **Object-Detecto** - Design inspiration
- **Web Speech API** - Voice control capabilities
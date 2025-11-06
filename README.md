# AI Mobility for the Blind

**AI-powered object detection system with voice control, designed to assist visually impaired users.**

This application combines a powerful FastAPI backend with YOLO object detection models and a fully voice-controlled frontend to provide real-time audio feedback about detected objects in uploaded videos or images.

---

## 🌟 Features

### Core Functionality
- **Custom YOLOv8n Object Detection**: Single optimized model detecting 4 essential classes:
  - Car
  - Person
  - Green Light
  - Zebra crossing
- **Video & Image Processing**: Upload videos or images for instant object detection with annotated output
- **Multi-Language TTS Audio Feedback**: Audio descriptions in English, Telugu (తెలుగు), and Hindi (हिंदी)
- **Adjustable Playback Speed**: Control audio speed (0.5x to 2x) for comfortable listening
- **Detection History**: Saves all detections with video/image and audio files organized by user and timestamp
- **User Authentication**: Secure user registration and login system with language preferences
- **Browser-Optimized Video Playback**: H.264 High Profile Level 4.1 encoded MP4s play smoothly in all modern browsers and VLC
- **Live Progress Tracking**: Real-time progress updates during video processing with voice announcements

### Voice Control (Hands-Free Operation)
- **Complete Voice Navigation**: Navigate the entire app using voice commands
- **Voice Form Input**: Fill login, registration, and feedback forms by voice
- **Audio/Video Playback Control**: Play, pause, and control detection media via voice
- **Speed Control Commands**: Change playback speed using voice
- **Real-time Feedback**: Voice confirmation and progress announcements for all actions

### Multi-Language Support
- **3 Languages**: English, Telugu (తెలుగు), Hindi (हिंदी)
- **Native Translations**: Complete sentence translations, not just accent changes
- **User Preference**: Set default language in profile/registration
- **Per-Upload Override**: Change language for individual video uploads
- **Zero Language Mixing**: Audio generated 100% in selected language

### Backend Integration
- **Automatic Backend Fallback**: Connects to DevTunnel (HTTPS) or falls back to local servers
- **RESTful API**: Well-structured endpoints for users, detection, and history
- **Background Processing**: Async video processing with real-time progress updates
- **Organized File Storage**: User files stored by username and timestamp
- **CORS Enabled**: Ready for cross-origin frontend requests
- **Error Handling**: Comprehensive error messages with user-friendly feedback

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

### 3) Set Up PostgreSQL Database

#### Install PostgreSQL (if not already installed)

**Windows:**
1. Download PostgreSQL from https://www.postgresql.org/download/windows/
2. Run the installer and remember the password you set for the `postgres` user
3. Add PostgreSQL's `bin` directory to your system PATH (usually `C:\Program Files\PostgreSQL\16\bin`)

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

**Linux:**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
```

#### Create the Database

Open PowerShell (Windows) or Terminal (macOS/Linux):

```powershell
# Connect to PostgreSQL as postgres user
psql -U postgres

# In the psql prompt, create the database:
CREATE DATABASE ai_mobility_db;

# List databases to verify (optional)
\l

# Exit psql
\q
```

Or create the database in one command:
```powershell
# Windows
psql -U postgres -c "CREATE DATABASE ai_mobility_db;"

# Linux/macOS (if you need sudo)
sudo -u postgres psql -c "CREATE DATABASE ai_mobility_db;"
```

### 3) Configure Backend Settings

Copy the example environment file and configure it:

```powershell
cd backend
copy .env.example .env
```

Then edit `backend/.env` file and update the PostgreSQL password:

```env
# Database connection - UPDATE WITH YOUR PASSWORD
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost/ai_mobility_db

# Custom YOLOv8n model path
MODEL_PATH=models/Yolov8n.pt

# Backend URLs (localhost for development)
Backend_PORT=http://localhost:8000
Backend_PORT_FALLBACK=http://localhost:8000

# Storage directories (auto-created)
HISTORY_STORAGE_DIR=storage/history
TEMP_UPLOAD_DIR=tmp/
```

**Important**: 
- Replace `YOUR_PASSWORD` with your PostgreSQL password
- Ensure `Yolov8n.pt` model file exists in the `backend/models/` directory

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
   - **Username, Email, Password** (by typing or voice)
   - **Select Language**: Choose English, Telugu (తెలుగు), or Hindi (हिंदी)
   - By voice: _"username is John"_, _"email is john at example dot com"_, _"password is mypassword"_, _"set language telugu"_, _"create account"_
4. Login with your credentials

### Uploading Media for Detection
1. Navigate to **Upload** page (click or say _"go to upload"_)
2. Select a video or image file
3. **(Optional)** Choose audio language override (default uses your profile language)
4. Say **"upload video"** or click the upload button
5. **Watch live progress** updates with voice announcements at 25%, 50%, 75%
6. Wait for detection to complete (audio in your selected language)
7. Listen to the audio summary or read the text results
8. **Adjust playback speed**: Use speed buttons (0.5x, 0.75x, 1x, 1.25x, 1.5x, 2x)
9. Control audio playback: _"play audio"_, _"pause"_

### Viewing Detection History
1. Go to **Detections** page (say _"go to detections"_)
2. View all your past detections with timestamps
3. Watch the detected videos directly in your browser (H.264 optimized)
4. **Adjust audio speed** with on-screen controls
5. Play any audio: _"play first audio"_, _"play audio number 2"_
6. Play videos: _"play video"_, _"play second video"_, _"pause video"_

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
- _"pause audio"_
- _"play first/second/third audio"_
- _"play audio number [X]"_

**Video Control (Detections Page)**
- _"play video"_ / _"play first video"_
- _"pause video"_
- _"play second/third video"_
- _"play video number [X]"_

**Profile Page**
- _"first name is [new name]"_
- _"update profile"_

**Feedback Page**
- _"feedback is [your feedback]"_
- _"submit feedback"_

**Settings Page**
- _"set language english"_ / _"set language telugu"_ / _"set language hindi"_
- _"save settings"_

**Audio Speed Control** (Detections Page)
- Click speed buttons: 0.5x, 0.75x, Normal (1x), 1.25x, 1.5x, 2x
- Voice announces speed changes

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
- `POST /detect/start` - Start async video/image detection (returns task_id)
- `GET /detect/progress/{task_id}` - Get real-time progress updates
- `POST /detect/{user_id}/with-audio` - Process video/image and return results with audio (with optional `lang` parameter)
- `POST /detect/image/{user_id}/with-audio` - Process image specifically (with optional `lang` parameter)
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
- **FastAPI** - Modern Python web framework with async support
- **SQLAlchemy** - ORM for database operations
- **PostgreSQL** - Relational database with user language preferences
- **Ultralytics YOLOv8** - Custom object detection model (4 classes)
- **gTTS** - Multi-language text-to-speech (English, Telugu, Hindi)
- **imageio-ffmpeg** - H.264 video encoding for browser compatibility
- **Pydantic** - Data validation and schemas

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
- Ensure `Yolov8n.pt` file exists in `backend/models/`
- Check MODEL_PATH in `.env` matches actual location
- Model file should be approximately 6-10 MB

**Video encoding warnings**
- Warnings about macro_block_size are now suppressed
- Level 4.1 High Profile supports 1080p video
- If issues persist, check imageio-ffmpeg installation: `pip install imageio-ffmpeg`

**Audio generation errors (Telugu/Hindi)**
- Ensure gTTS supports the language code: 'en', 'te', 'hi'
- Check internet connection (gTTS requires internet)
- If audio is mixed language, restart backend server

### Frontend Issues

**Voice control not working**
- Use Chrome or Edge (best Web Speech API support)
- Allow microphone permissions when prompted
- Check browser console for errors

**"Not logged in" errors**
- Clear browser localStorage: `localStorage.clear()` in console
- Register and login again

**Audio not playing**
- Check browser console for audio loading errors
- Verify CORS is enabled in backend
- Try different playback speed (use speed buttons)
- Check if audio file was generated: look in backend logs

**Video not playing**
- Ensure video is H.264 encoded (check backend logs for encoding codec)
- Try clearing browser cache: Ctrl+Shift+Delete
- Check video URL in browser console
- Try opening video URL directly in browser

**Progress bar stuck**
- Check backend terminal for processing errors
- Refresh page and try again
- Check if backend is still running

**Backend connection fails**
- Ensure backend is running on port 8000
- Check if port 8000 is already in use: `netstat -ano | findstr :8000`
- Verify backend URL in `frontend/js/config.js` is set to `http://localhost:8000`

### Language Issues

**Mixed English-Telugu/Hindi audio**
- Restart backend server to load latest translation fixes
- Clear detection history: `python backend\clear_database.py`
- Re-upload video with correct language selected

**Language not saving**
- Check if database migration ran: column `users.language` should exist
- Run: `python backend\add_language_column.py` if needed
- Verify language selection in registration/settings

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
- **Video Encoding**: H.264 High Profile Level 4.1 for optimal browser compatibility
- **Multi-Language**: Complete native translations for Telugu and Hindi (no mixed audio)
- **Playback Speed**: Adjustable from 0.5x to 2x for audio comfort

---

## 📄 License

See LICENSE file for details.

---

## 🙏 Acknowledgments

- **Ultralytics YOLOv8** - Object detection models
- **FastAPI** - Backend framework
- **Object-Detecto** - Design inspiration
- **Web Speech API** - Voice control capabilities
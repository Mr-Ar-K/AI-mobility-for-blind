# AI-mobility-for-blind

Simple, step-by-step instructions to set up and run the app on Windows (PowerShell).

## Prerequisites

- Python 3.10+
- Optional: Anaconda/Miniconda (for Conda environments)
- PostgreSQL running locally with a database named `ai_mobility_db`

## 1) Create and activate a virtual environment

Pick ONE of the options below.

### Option A — Conda (recommended)

```powershell
conda create -p .\venv python=3.10 -y
conda activate .\venv
```

### Option B — Python venv

```powershell
py -3.10 -m venv .venv
\.\.venv\Scripts\Activate.ps1
```

## 2) Install dependencies

```powershell
pip install -r requirements.txt
```

## 3) Configure backend settings

Edit `backend/.env` and set your actual database URL and model path, for example:

```
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost/ai_mobility_db
MODEL_PATH=models/best.pt
```

Also ensure the YOLO model file exists at `backend/models/best.pt`.

## 4) Start the backend server (FastAPI)

```powershell
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

If `uvicorn` is not recognized, run:

```powershell
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

## 5) Start the frontend (static server)

Open a NEW terminal (keep the backend running), activate the same environment again, then:

```powershell
cd frontend
python -m http.server 8080
```

Frontend: http://localhost:8080

## 6) Use the app

- Open http://localhost:8080
- Sign up, then log in
- Go to detection page and upload a video
- View detection history in the profile page

## 7) Stop servers and deactivate environment

- Press Ctrl+C in each terminal to stop servers
- Deactivate env:

Conda:
```powershell
conda deactivate
```

Python venv:
```powershell
deactivate
```

## Troubleshooting (quick)

- "uvicorn not recognized": ensure the environment is active; run `python -m uvicorn ...` or `pip install uvicorn[standard]` in the active env
- PostgreSQL auth errors: confirm `DATABASE_URL` in `backend/.env` has the right username/password and that `ai_mobility_db` exists
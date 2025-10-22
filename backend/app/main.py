from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO

from .core.config import settings
from .db import database, models
from .routers import users, history, detection

# Create all database tables
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="AI-Mobility-for-Blind Backend")

# --- CORS Middleware ---
# This allows your frontend (running on a different port) to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# --- Load Model at Startup ---
@app.on_event("startup")
def load_model():
    print(f"Loading model from: {settings.MODEL_PATH}")
    app.state.model = YOLO(settings.MODEL_PATH)
    print("Model loaded successfully.")

# --- Include Routers ---
app.include_router(users.router)
app.include_router(history.router)
app.include_router(detection.router)

@app.get("/")
def read_root():
    return {"message": "AI-Mobility-for-Blind Backend is running."}

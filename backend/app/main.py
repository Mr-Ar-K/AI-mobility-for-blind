from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from ultralytics import YOLO
import torch
import asyncio
from collections import deque
import os

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

# GZip compression for faster transfers of JSON and other responses
app.add_middleware(GZipMiddleware, minimum_size=500)

# --- Initialize Task Queue for Multi-User Processing ---
app.state.task_queue = deque()  # FIFO queue for processing tasks
app.state.processing_lock = asyncio.Lock()  # Legacy lock (unused with semaphore)
app.state.queue_enabled = True
app.state.max_concurrency = max(1, (os.cpu_count() or 2) // 2)  # Conservative on CPU-only
app.state.semaphore = asyncio.Semaphore(app.state.max_concurrency)

# --- Load All Three Models at Startup ---
@app.on_event("startup")
def load_model():
    print("Loading multi-model detection system...")
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}")
    print("✅ Multi-user task queue initialized")
    
    # Model 1: YOLOv8m (for general objects - cars, people, etc.)
    print(f"Loading YOLOv8m model from: {settings.MODEL_PATH_YOLO}")
    app.state.model_yolo = YOLO(settings.MODEL_PATH_YOLO)
    try:
        app.state.model_yolo.to(device)
        # Fuse Conv+BN for speed and use half precision on CUDA when available
        try:
            app.state.model_yolo.fuse()
        except Exception:
            pass
        if device == 'cuda':
            try:
                app.state.model_yolo.model.half()
            except Exception:
                pass
    except Exception as _:
        pass
    print("✅ YOLOv8m model loaded successfully.")
    
    # Model 2: Traffic Lights specialist
    print(f"Loading Traffic Lights model from: {settings.MODEL_PATH_TRAFFIC_LIGHTS}")
    app.state.model_lights = YOLO(settings.MODEL_PATH_TRAFFIC_LIGHTS)
    try:
        app.state.model_lights.to(device)
        try:
            app.state.model_lights.fuse()
        except Exception:
            pass
        if device == 'cuda':
            try:
                app.state.model_lights.model.half()
            except Exception:
                pass
    except Exception as _:
        pass
    print("✅ Traffic Lights model loaded successfully.")
    
    # Model 3: Zebra Crossing specialist
    print(f"Loading Zebra Crossing model from: {settings.MODEL_PATH_ZEBRA_CROSSING}")
    app.state.model_zebra = YOLO(settings.MODEL_PATH_ZEBRA_CROSSING)
    try:
        app.state.model_zebra.to(device)
        try:
            app.state.model_zebra.fuse()
        except Exception:
            pass
        if device == 'cuda':
            try:
                app.state.model_zebra.model.half()
            except Exception:
                pass
    except Exception as _:
        pass
    print("✅ Zebra Crossing model loaded successfully.")
    
    print("🎉 All models loaded successfully!")

# --- Include Routers ---
app.include_router(users.router)
app.include_router(history.router)
app.include_router(detection.router)

@app.get("/")
def read_root():
    return {"message": "AI-Mobility-for-Blind Backend is running."}

@app.get("/config")
def get_config():
    """Return backend configuration for frontend"""
    return {
        "backend_url": settings.Backend_PORT,
        "backend_fallback": settings.Backend_PORT_FALLBACK
    }

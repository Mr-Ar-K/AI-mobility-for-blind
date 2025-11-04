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


import logging
app = FastAPI(title="AI-Mobility-for-Blind Backend")

# --- Optimized Logging Middleware ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Log only essential info for performance (removed verbose header logging)
    logging.info(f"Incoming request: {request.method} {request.url.path}")
    response = await call_next(request)
    return response

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

# --- Load Single Custom Model at Startup ---
@app.on_event("startup")
def load_model():
    print("Loading custom YOLOv8n detection model...")
    
    # Auto-select best available device (GPU or CPU)
    if torch.cuda.is_available():
        device = 'cuda'
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        print(f"🚀 GPU detected: {gpu_name} ({gpu_memory:.2f} GB)")
        print(f"Using device: {device}")
    else:
        device = 'cpu'
        cpu_count = os.cpu_count() or 1
        print(f"💻 Using CPU with {cpu_count} cores")
        print(f"Using device: {device}")
    
    print("✅ Multi-user task queue initialized")
    
    # Load Custom YOLOv8n Model: Car, Person, Green Light, zebra crossing
    print(f"Loading custom YOLOv8n model from: {settings.MODEL_PATH}")
    app.state.model = YOLO(settings.MODEL_PATH)
    
    try:
        app.state.model.to(device)
        
        # Optimize model for performance
        try:
            app.state.model.fuse()  # Fuse Conv+BN layers for speed
            print("✅ Model layers fused for optimized inference")
        except Exception as e:
            print(f"⚠️  Layer fusion skipped: {e}")
        
        # Use half precision (FP16) on CUDA for faster inference
        if device == 'cuda':
            try:
                app.state.model.model.half()
                print("✅ FP16 (half precision) enabled for faster GPU inference")
            except Exception as e:
                print(f"⚠️  FP16 optimization skipped: {e}")
        
        # Set optimal number of threads for CPU
        if device == 'cpu':
            torch.set_num_threads(max(1, (os.cpu_count() or 2) // 2))
            print(f"✅ CPU threads optimized: {torch.get_num_threads()} threads")
            
    except Exception as e:
        print(f"⚠️  Model optimization failed: {e}")
    
    print("🎉 Custom YOLOv8n model loaded and optimized successfully!")
    print("📊 Model detects: Car, Person, Green Light, zebra crossing")

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

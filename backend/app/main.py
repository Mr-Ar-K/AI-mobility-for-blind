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

# --- Load All Three Models at Startup ---
@app.on_event("startup")
def load_model():
    print("Loading multi-model detection system...")
    
    # Model 1: YOLOv8m (for general objects - cars, people, etc.)
    print(f"Loading YOLOv8m model from: {settings.MODEL_PATH_YOLO}")
    app.state.model_yolo = YOLO(settings.MODEL_PATH_YOLO)
    print("✅ YOLOv8m model loaded successfully.")
    
    # Model 2: Traffic Lights specialist
    print(f"Loading Traffic Lights model from: {settings.MODEL_PATH_TRAFFIC_LIGHTS}")
    app.state.model_lights = YOLO(settings.MODEL_PATH_TRAFFIC_LIGHTS)
    print("✅ Traffic Lights model loaded successfully.")
    
    # Model 3: Zebra Crossing specialist
    print(f"Loading Zebra Crossing model from: {settings.MODEL_PATH_ZEBRA_CROSSING}")
    app.state.model_zebra = YOLO(settings.MODEL_PATH_ZEBRA_CROSSING)
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

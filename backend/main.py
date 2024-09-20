# backend/main.py

import os
import uuid
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from supabase import create_client, Client
import logging

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="YouTube Video Processor API",
    description="API for processing YouTube videos, retrieving comments, transcribing, and generating tags.",
    version="1.0.0"
)

# Setup CORS middleware to allow frontend access
origins = [
    "*",  # In production, specify the exact origin
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Dictionary to manage active WebSocket connections
active_connections = {}

@app.post("/process")
async def initiate_processing(data: dict, background_tasks: BackgroundTasks):
    """
    Endpoint to initiate the processing of YouTube videos.
    """
    # Import process_videos here
    from tasks import process_videos
    
    # Generate a unique session ID
    session_id = str(uuid.uuid4())

    # Extract data from request
    video_ids = data.get("video_ids", [])
    num_videos = data.get("num_videos", 10)
    num_comments = data.get("num_comments", 50)
    num_tags = data.get("num_tags", 5)
    clustering_strength = data.get("clustering_strength", 0.3)

    # Start background task for processing
    background_tasks.add_task(
        process_videos,
        session_id,
        supabase,
        video_ids,
        num_videos,
        num_comments,
        num_tags,
        clustering_strength
    )

    # Return the session ID to the client
    return {"session_id": session_id}

@app.post("/process")
async def initiate_processing(data: dict, background_tasks: BackgroundTasks):
    try:
        # Your existing code here
        return {"session_id": session_id}
    except Exception as e:
        logging.error(f"Error in initiate_processing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time updates.
    """
    await websocket.accept()

    # Add connection to active_connections
    if session_id not in active_connections:
        active_connections[session_id] = []
    active_connections[session_id].append(websocket)

    try:
        while True:
            # Keep the connection open
            await websocket.receive_text()
    except WebSocketDisconnect:
        # Remove connection on disconnect
        active_connections[session_id].remove(websocket)
        if not active_connections[session_id]:
            del active_connections[session_id]

def send_update(session_id: str, message: str):
    """
    Function to send updates to all active WebSocket connections for a session.
    """
    if session_id in active_connections:
        for connection in active_connections[session_id]:
            try:
                connection.send_json({"message": message})
            except:
                pass  # Handle broken connections silently

@app.get("/")
async def root():
    return {"message": "Welcome to YouTube Video Processor API"}
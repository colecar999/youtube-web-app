# backend/main.py

import os
import uuid
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from supabase import create_client, Client
import logging
from typing import List
from utils import send_update
from tasks import process_videos

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

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add ConnectionManager as before
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# Update the initiate_processing function
@app.post("/process")
async def initiate_processing(data: dict, background_tasks: BackgroundTasks):
    try:
        session_id = str(uuid.uuid4())
        logger.info(f"Initiating processing for session {session_id}")
        
        # Extract data from request
        video_ids = data.get("video_ids", [])
        num_videos = data.get("num_videos", 10)
        num_comments = data.get("num_comments", 50)
        num_tags = data.get("num_tags", 5)
        clustering_strength = data.get("clustering_strength", 0.3)

        logger.info(f"Processing parameters: video_ids={video_ids}, num_videos={num_videos}, num_comments={num_comments}, num_tags={num_tags}, clustering_strength={clustering_strength}")

        # Send initial update
        await send_update(manager, session_id, "Processing started. Waiting for updates...", supabase)

        # Start background task for processing
        logger.info(f"Starting background task for session {session_id}")
        background_tasks.add_task(
            process_videos,
            manager,
            session_id,
            supabase,
            video_ids,
            num_videos,
            num_comments,
            num_tags,
            clustering_strength
        )

        return {"session_id": session_id}
    except Exception as e:
        logger.exception(f"Error in initiate_processing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint if still needed
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket)
    try:
        logger.info(f"WebSocket connection opened for client {client_id}")
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received message from client {client_id}: {data}")
            await send_update(manager, client_id, f"Message received: {data}")
    except WebSocketDisconnect:
        logger.info(f"WebSocket connection closed for client {client_id}")
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Error in WebSocket connection for client {client_id}: {str(e)}")
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
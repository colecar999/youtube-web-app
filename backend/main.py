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
logging.basicConfig(level=logging.INFO)
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

@app.post("/process")
async def initiate_processing(data: dict, background_tasks: BackgroundTasks):
    try:
        session_id = str(uuid.uuid4())
        background_tasks.add_task(process_videos, session_id, supabase, **data)
        return {"session_id": session_id}
    except Exception as e:
        logger.error(f"Error in initiate_processing: {str(e)}")
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
            await manager.broadcast(f"Message from client {client_id}: {data}")
    except WebSocketDisconnect:
        logger.info(f"WebSocket connection closed for client {client_id}")
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Error in WebSocket connection for client {client_id}: {str(e)}")
        manager.disconnect(websocket)

# The rest of your main.py remains unchanged
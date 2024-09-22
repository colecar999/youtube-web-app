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

# Update the initiate_processing function
@app.post("/process")
async def initiate_processing(request: dict, background_tasks: BackgroundTasks):
    try:
        session_id = str(uuid.uuid4())
        logger.info(f"Initiating processing for session {session_id}")
        
        # Extract data from request
        video_ids = request.get("video_ids", [])
        num_videos = request.get("num_videos", 10)
        num_comments = request.get("num_comments", 50)
        num_tags = request.get("num_tags", 5)
        clustering_strength = request.get("clustering_strength", 0.3)

        logger.info(f"Processing parameters: video_ids={video_ids}, num_videos={num_videos}, num_comments={num_comments}, num_tags={num_tags}, clustering_strength={clustering_strength}")

        # Send initial update
        success = await send_update(session_id, "Processing started. Waiting for updates...", supabase)
        if not success:
            logger.error(f"Failed to send initial update for session {session_id}")
            # You might want to handle this failure, perhaps by raising an exception

        # Start background task for processing
        logger.info(f"Starting background task for session {session_id}")
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

        return {"session_id": session_id}
    except Exception as e:
        logger.exception(f"Error in initiate_processing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
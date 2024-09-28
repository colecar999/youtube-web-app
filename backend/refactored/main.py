# backend/main.py

import os
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from supabase import create_client, Client

from config import SUPABASE_URL, SUPABASE_KEY, ORIGINS
from utils.logging_config import setup_logging
from utils.helpers import send_update
from tasks.video_processing import process_videos

# Load environment variables and setup logging
load_dotenv()
logger = setup_logging()

# Initialize FastAPI app
app = FastAPI(
    title="YouTube Video Processor API",
    description="API for processing YouTube videos, retrieving comments, transcribing, and generating tags.",
    version="1.0.0"
)

# Setup CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

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
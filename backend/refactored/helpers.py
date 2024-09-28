# backend/utils/helpers.py

import json
import logging
from supabase import Client
import datetime

logger = logging.getLogger(__name__)

async def send_update(session_id: str, message: str, supabase: Client):
    logger.info(f"Attempting to send update for session {session_id}: {message}")
    
    try:
        result = supabase.table('updates').insert({
            "session_id": session_id,
            "message": message,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }).execute()
        
        # If the result is awaitable, await it
        if hasattr(result, '__await__'):
            await result
        
        logger.info(f"Update successfully sent via Supabase for session {session_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to send Supabase update for session {session_id}: {str(e)}")
        return False
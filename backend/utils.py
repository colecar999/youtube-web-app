import json
import logging
from supabase import Client
import datetime

logger = logging.getLogger(__name__)

async def send_update(manager, session_id: str, message: str, supabase: Client):
    try:
        logger.info(f"Sending update for session {session_id}: {message}")
        
        # Send update through WebSocket
        await manager.broadcast(json.dumps({"session_id": session_id, "message": message}))
        logger.debug(f"Broadcast message sent for session {session_id}")
        
        # Send update through Supabase
        result = supabase.table('updates').insert({
            "session_id": session_id,
            "message": message,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }).execute()
        
        # If the result is awaitable, await it
        if hasattr(result, '__await__'):
            await result
        
        logger.info(f"Update sent to Supabase for session {session_id}: {message}")
    except Exception as e:
        logger.exception(f"Error in send_update for session {session_id}: {str(e)}")
        logger.error(f"Failed to send update: session_id={session_id}, message={message}")
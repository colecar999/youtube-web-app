import json
import logging
from supabase import Client
import datetime

logger = logging.getLogger(__name__)

async def send_update(manager, session_id: str, message: str, supabase: Client):
    logger.info(f"Attempting to send update for session {session_id}: {message}")
    
    websocket_success = False
    supabase_success = False

    # Send update through WebSocket
    try:
        await manager.broadcast(json.dumps({"session_id": session_id, "message": message}))
        logger.debug(f"Broadcast message sent via WebSocket for session {session_id}")
        websocket_success = True
    except Exception as e:
        logger.error(f"Failed to send WebSocket update for session {session_id}: {str(e)}")

    # Send update through Supabase
    try:
        result = supabase.table('updates').insert({
            "session_id": session_id,
            "message": message,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }).execute()
        
        # If the result is awaitable, await it
        if hasattr(result, '__await__'):
            await result
        
        logger.debug(f"Update sent to Supabase for session {session_id}")
        supabase_success = True
    except Exception as e:
        logger.error(f"Failed to send Supabase update for session {session_id}: {str(e)}")

    if websocket_success and supabase_success:
        logger.info(f"Update successfully sent via both WebSocket and Supabase for session {session_id}")
    elif websocket_success:
        logger.warning(f"Update sent via WebSocket only for session {session_id}")
    elif supabase_success:
        logger.warning(f"Update sent via Supabase only for session {session_id}")
    else:
        logger.error(f"Failed to send update via both WebSocket and Supabase for session {session_id}")

    return websocket_success or supabase_success
import json
import logging
from supabase import Client
import datetime

async def send_update(manager, session_id: str, message: str, supabase: Client):
    try:
        # Send update through WebSocket
        await manager.broadcast(json.dumps({"session_id": session_id, "message": message}))
        
        # Send update through Supabase
        result = supabase.table('updates').insert({
            "session_id": session_id,
            "message": message,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }).execute()
        
        # If the result is awaitable, await it
        if hasattr(result, '__await__'):
            await result
        
        logging.info(f"Update sent to Supabase: {message}")
    except Exception as e:
        logging.error(f"Error in send_update: {str(e)}")
        logging.error(f"Failed to send update: session_id={session_id}, message={message}")
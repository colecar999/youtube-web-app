import json
import logging
from supabase import Client
import datetime

async def send_update(manager, session_id: str, message: str, supabase: Client):
    try:
        # Send update through WebSocket
        await manager.broadcast(json.dumps({"session_id": session_id, "message": message}))
        
        # Send update through Supabase
        result = await supabase.table('updates').insert({
            "session_id": session_id,
            "message": message
        }).execute()
        logging.info(f"Update sent to Supabase: {result}")
    except Exception as e:
        logging.error(f"Error in send_update: {str(e)}")
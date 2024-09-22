import json
import logging
from supabase import Client

async def send_update(manager, session_id: str, message: str, supabase: Client):
    try:
        # Send update through WebSocket
        await manager.broadcast(json.dumps({"session_id": session_id, "message": message}))
        
        # Send update through Supabase
        result = await supabase.table('updates').insert({
            "session_id": session_id,
            "message": message,
            "timestamp": supabase.table('updates').select('now()').execute().data[0]['now']
        }).execute()
        logging.info(f"Update sent to Supabase: {result}")
    except Exception as e:
        logging.error(f"Error in send_update: {str(e)}")
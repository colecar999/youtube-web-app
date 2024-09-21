import json

async def send_update(manager, session_id: str, message: str):
    await manager.broadcast(json.dumps({"session_id": session_id, "message": message}))
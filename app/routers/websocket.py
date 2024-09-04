from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.websocket_manager import WebSocketManager
from app.services.message_service import MessageService
from app.schemas.message import Message

router = APIRouter()
websocket_manager = WebSocketManager()
message_service = MessageService()

@router.websocket("/ws/{chamber_id}")
async def websocket_endpoint(websocket: WebSocket, chamber_id: str):
    """
    WebSocket endpoint for real-time communication within a chamber.
    
    Args:
        websocket (WebSocket): The WebSocket connection.
        chamber_id (str): The ID of the chamber.
    """
    await websocket_manager.connect(websocket, chamber_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = Message(content=data, chamber_id=chamber_id)
            await message_service.save_message(message)
            await websocket_manager.broadcast(message, chamber_id)
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, chamber_id)
        await websocket_manager.broadcast(f"Client left the chamber", chamber_id)

@router.get("/messages/{chamber_id}")
async def get_messages(chamber_id: str):
    """
    Retrieve messages for a specific chamber.
    
    Args:
        chamber_id (str): The ID of the chamber.
    
    Returns:
        List[Message]: A list of messages for the specified chamber.
    """
    return await message_service.get_messages(chamber_id)
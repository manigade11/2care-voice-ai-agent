from fastapi import APIRouter, WebSocket
from backend.controllers.websocket_controller import voice_agent_websocket

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/voice")
async def websocket_voice_endpoint(websocket: WebSocket):
    await voice_agent_websocket(websocket)
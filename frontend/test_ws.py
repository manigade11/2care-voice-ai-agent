import asyncio
import json
import websockets

async def main():
    uri = "ws://127.0.0.1:8000/api/ws/voice"
    async with websockets.connect(uri) as websocket:
        payload = {
            "session_id": "session_101",
            "patient_id": "patient_001",
            "text": "Book appointment with cardiologist tomorrow at 10:30"
        }
        await websocket.send(json.dumps(payload))
        response = await websocket.recv()
        print(response)

asyncio.run(main())
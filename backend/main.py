from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# allow any origin for development ease
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active.append(websocket)
        try:
            client = websocket.client if hasattr(websocket, 'client') else None
        except Exception:
            client = None
        print(f"WebSocket connected: {client} — total connections: {len(self.active)}")

    def disconnect(self, websocket: WebSocket):
        try:
            self.active.remove(websocket)
        except ValueError:
            pass
        try:
            client = websocket.client if hasattr(websocket, 'client') else None
        except Exception:
            client = None
        print(f"WebSocket disconnected: {client} — total connections: {len(self.active)}")

    async def broadcast(self, message: str):
        # send text message to all connected clients
        print(f"Broadcasting message to {len(self.active)} connections: {message}")
        for connection in list(self.active):
            try:
                await connection.send_text(message)
            except Exception:
                # ignore send errors
                pass


manager = ConnectionManager()


@app.get("/")
async def root():
    return {"status": "ok", "msg": "WebSocket server running"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # simple broadcast behavior: echo to all
            await manager.broadcast(data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)


from voice.vad_ws import register_vad

register_vad(app)

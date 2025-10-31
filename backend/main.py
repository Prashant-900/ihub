from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
import os
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

    def disconnect(self, websocket: WebSocket):
        try:
            self.active.remove(websocket)
        except ValueError:
            pass

    async def broadcast(self, message: str):
        # send text message to all connected clients
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


# serve cache directory for audio files
CACHE_DIR = os.path.join(os.path.dirname(__file__), 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)
app.mount('/cache', StaticFiles(directory=CACHE_DIR), name='cache')


@app.get('/audio/{filename}')
async def stream_audio(filename: str):
    """Stream an audio file from the cache directory. Filename should include extension."""
    # sanitize filename to avoid path traversal
    safe_name = os.path.basename(filename)
    path = os.path.join(CACHE_DIR, safe_name)

    # Use FileResponse which supports efficient file serving
    from fastapi.responses import FileResponse

    # if file not found exactly, try to resolve common extensions or files that start with the id
    if not os.path.exists(path):
        candidates = []
        try:
            for f in os.listdir(CACHE_DIR):
                if f.startswith(safe_name):
                    candidates.append(f)
        except Exception:
            candidates = []
        if candidates:
            chosen = candidates[0]
            path = os.path.join(CACHE_DIR, chosen)
        else:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail='Audio not found')

    # attempt to set correct mime type based on extension
    import mimetypes
    mime_type, _ = mimetypes.guess_type(path)
    try:
        return FileResponse(path, media_type=mime_type or 'application/octet-stream', filename=os.path.basename(path))
    except Exception:
        return FileResponse(path, filename=os.path.basename(path))


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


# Admin endpoint to fetch conversation history
try:
    # package mode
    from .database import db
except Exception:
    # script/module mode
    from database import db


@app.get('/admin/conversations')
async def admin_conversations(limit: int = 100):
    """Return recent messages and AI responses merged by created time (most recent first)."""
    msgs = db.get_messages(limit=limit)
    ais = db.get_ai_responses(limit=limit)

    # Normalize rows with created_at
    def normalize_msg(m):
        return {
            'type': 'message',
            'id': m.get('id'),
            'text': m.get('text'),
            'created_at': m.get('created_at')
        }

    def normalize_ai(a):
        return {
            'type': 'ai_response',
            'id': a.get('id'),
            'text': a.get('text'),
            'timeline': a.get('timeline'),
            'audio_id': a.get('audio_id'),
            'created_at': a.get('created_at')
        }

    combined = [normalize_msg(m) for m in msgs] + [normalize_ai(a) for a in ais]
    # sort by created_at descending (DB stores ISO timestamps)
    try:
        combined.sort(key=lambda x: x.get('created_at') or '', reverse=True)
    except Exception:
        pass
    return {'items': combined}


try:
    from vad_ws import register_vad
except ImportError:
    from .vad_ws import register_vad

<<<<<<< HEAD
try:
    from video_ws import register_video
except ImportError:
    from .video_ws import register_video

register_video(app)
=======
register_vad(app, manager)
>>>>>>> main

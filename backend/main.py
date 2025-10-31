from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
import os
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="iHub AI Character Assistant",
    description="AI character animation with speech recognition and text-to-speech",
    version="1.0.0"
)

# Configure CORS for production
allowed_origins = os.environ.get('ALLOWED_ORIGINS', '*').split(',')
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=3600
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
    """Stream an audio file from the cache directory.
    
    Args:
        filename: Audio filename (with or without extension)
        
    Returns:
        FileResponse with appropriate content type
        
    Raises:
        HTTPException(404): When file is not found
    """
    from fastapi.responses import FileResponse
    from fastapi import HTTPException
    import mimetypes

    # Sanitize filename to prevent path traversal attacks
    safe_name = os.path.basename(filename)
    if not safe_name:
        raise HTTPException(status_code=400, detail='Invalid filename')

    # Attempt to find file
    path = os.path.join(CACHE_DIR, safe_name)
    if not os.path.exists(path):
        # Try to find files that start with the requested name (handle missing extensions)
        try:
            candidates = [f for f in os.listdir(CACHE_DIR) if f.startswith(safe_name)]
            if candidates:
                path = os.path.join(CACHE_DIR, candidates[0])
            else:
                raise HTTPException(status_code=404, detail='Audio file not found')
        except (OSError, FileNotFoundError):
            raise HTTPException(status_code=404, detail='Audio file not found')

    # Verify the file is within cache directory (security check)
    try:
        resolved_path = os.path.abspath(path)
        cache_dir_abs = os.path.abspath(CACHE_DIR)
        if not resolved_path.startswith(cache_dir_abs):
            raise HTTPException(status_code=403, detail='Access denied')
    except (OSError, ValueError):
        raise HTTPException(status_code=403, detail='Access denied')

    # Determine MIME type
    mime_type, _ = mimetypes.guess_type(path)
    mime_type = mime_type or 'application/octet-stream'

    try:
        return FileResponse(
            path,
            media_type=mime_type,
            filename=os.path.basename(path)
        )
    except (OSError, FileNotFoundError):
        raise HTTPException(status_code=404, detail='Audio file not accessible')


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

try:
    from video_ws import register_video
except ImportError:
    from .video_ws import register_video

register_video(app)
register_vad(app, manager)

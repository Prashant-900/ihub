from fastapi import WebSocket, WebSocketDisconnect
import json
import base64
import numpy as np
import time
import torch
from pipeline.pipeline import Pipeline
from database import db
import os
import uuid

def register_vad(app, manager=None):
    @app.websocket("/ws-vad")
    async def websocket_vad(websocket: WebSocket):
        await websocket.accept()

        device = torch.device("cpu")
        pipeline = Pipeline(device=device)

        speaking = False
        speech_start = 0.0
        silence_frames = 0
        speech_frames = 0
        SPEECH_THRESHOLD = 3
        SILENCE_THRESHOLD = 8
        RMS_THRESHOLD = 0.01
        audio_buffer = []
        response_mode = 'audio'  # Track current response mode for audio input

        try:
            while True:
                try:
                    msg = await websocket.receive_text()
                except WebSocketDisconnect:
                    break

                try:
                    payload = json.loads(msg)
                    if payload.get("type") == "text":
                        user_text = payload.get('text', '')
                        response_mode = payload.get('responseMode', 'audio')  # Update current response mode
                        try:
                            result = pipeline.handle_input(audio_frames=[], user_text=user_text, response_mode=response_mode)
                            # send user_message event
                            try:
                                user_ev = {
                                    'event': 'user_message',
                                    'text': user_text or result.get('user_text') or '',
                                    'created_at': (result.get('user_row') or {}).get('created_at') if result.get('user_row') else None,
                                }
                                await websocket.send_text(json.dumps(user_ev))
                            except Exception:
                                pass
                            # send ai_response event
                            try:
                                ai_payload = {
                                    'event': 'ai_response',
                                    'response': result.get('ai_text'),
                                    'timeline': result.get('timeline'),
                                    'audio_id': result.get('audio_id'),
                                    'text': result.get('text'),
                                    'responseMode': response_mode,
                                    'created_at': (result.get('ai_row') or {}).get('created_at') if result.get('ai_row') else None,
                                }
                                await websocket.send_text(json.dumps(ai_payload))
                            except Exception:
                                pass
                        except Exception:
                            pass
                        continue
                    if payload.get("type") != "audio":
                        continue

                    sr_rate = int(payload.get("sampleRate", 16000))
                    b64 = payload.get("data")
                    if not b64:
                        continue

                    raw = base64.b64decode(b64)
                    pcm = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
                    audio_buffer.append(pcm)

                    rms = np.sqrt(np.mean(pcm**2)) if pcm.size > 0 else 0.0
                    if rms > RMS_THRESHOLD:
                        speech_frames += 1
                        silence_frames = 0
                    else:
                        silence_frames += 1
                        speech_frames = 0

                    is_speech = speech_frames >= SPEECH_THRESHOLD

                    if is_speech:
                        if not speaking:
                            speaking = True
                            speech_start = time.time()
                            await websocket.send_text(json.dumps({"event": "speech_started"}))
                            # Broadcast to all general /ws connections so all frontend components can react
                            if manager:
                                await manager.broadcast(json.dumps({"event": "speech_started"}))
                        silence_frames = 0
                    else:
                        if speaking and silence_frames >= SILENCE_THRESHOLD:
                            speaking = False
                            duration = time.time() - speech_start

                            # Process audio through pipeline
                            # Concatenate audio and create user message record
                            if len(audio_buffer) == 0:
                                user_audio = np.array([], dtype=np.float32)
                            else:
                                user_audio = np.concatenate(audio_buffer)

                            # Transcribe and handle via pipeline
                            try:
                                result = pipeline.handle_input(audio_frames=audio_buffer, user_text=None, response_mode=response_mode)
                                # send user_message event
                                try:
                                    user_ev = {
                                            'event': 'user_message',
                                            'text': (result.get('user_row') or {}).get('text') if result.get('user_row') else (result.get('user_text') or ''),
                                            'created_at': (result.get('user_row') or {}).get('created_at') if result.get('user_row') else None,
                                        }
                                    await websocket.send_text(json.dumps(user_ev))
                                except Exception:
                                    pass
                                # send ai_response event
                                try:
                                    ai_payload = {
                                        'event': 'ai_response',
                                        'response': result.get('ai_text'),
                                        'timeline': result.get('timeline'),
                                        'audio_id': result.get('audio_id'),
                                        'text': result.get('text'),
                                        'responseMode': 'audio',
                                        'duration': duration,
                                        'created_at': (result.get('ai_row') or {}).get('created_at') if result.get('ai_row') else None,
                                    }
                                    await websocket.send_text(json.dumps(ai_payload))
                                except Exception:
                                    pass
                            except Exception:
                                pass

                            audio_buffer = []
                            speech_frames = 0
                            silence_frames = 0

                except Exception:
                    continue
        finally:
            pass

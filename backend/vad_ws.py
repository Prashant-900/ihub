from fastapi import WebSocket, WebSocketDisconnect
import json
import base64
import numpy as np
import time
import torch
from pipeline.pipeline import Pipeline

def register_vad(app):
    @app.websocket("/ws-vad")
    async def websocket_vad(websocket: WebSocket):
        await websocket.accept()
        print("VAD socket connected")

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

        try:
            while True:
                try:
                    msg = await websocket.receive_text()
                except WebSocketDisconnect:
                    print("VAD socket disconnected by client")
                    break

                try:
                    payload = json.loads(msg)
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
                            print("VAD: speech started")
                            await websocket.send_text(json.dumps({"event": "speech_started"}))
                        silence_frames = 0
                    else:
                        if speaking and silence_frames >= SILENCE_THRESHOLD:
                            speaking = False
                            duration = time.time() - speech_start
                            print(f"VAD: speech ended, duration={duration:.2f}s")

                            # Process audio through pipeline
                            response = pipeline.process_audio(audio_buffer)
                            response.update({
                                "event": "speech_ended",
                                "duration": duration
                            })
                            await websocket.send_text(json.dumps(response))

                            audio_buffer = []
                            speech_frames = 0
                            silence_frames = 0

                except Exception as e:
                    print("Error processing audio:", e)
                    continue
        finally:
            print("VAD socket closed")

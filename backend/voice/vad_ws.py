from fastapi import WebSocket, WebSocketDisconnect
import json
import base64
import numpy as np
import time
import torch
from .stt_model import load_stt_model


def register_vad(app):
    @app.websocket("/ws-vad")
    async def websocket_vad(websocket: WebSocket):
        await websocket.accept()
        print("VAD socket connected")

        device = torch.device('cpu')
        model, decoder, utils = load_stt_model(device=device)

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
                msg = await websocket.receive_text()
                try:
                    payload = json.loads(msg)
                    if payload.get("type") != "audio":
                        continue

                    sr_rate = int(payload.get("sampleRate", 16000))
                    b64 = payload.get("data")
                    if not b64:
                        continue

                    raw = base64.b64decode(b64)
                    # Expect incoming frames as PCM16 little-endian
                    pcm = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

                    # Append to buffer for STT
                    audio_buffer.append(pcm)

                    # RMS VAD detection
                    rms = np.sqrt(np.mean(pcm**2)) if pcm.size > 0 else 0.0
                    if rms > RMS_THRESHOLD:
                        speech_frames += 1
                        silence_frames = 0
                    else:
                        silence_frames += 1
                        speech_frames = 0

                    is_speech = speech_frames >= SPEECH_THRESHOLD

                    # ----- Speech state handling -----
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

                            # Prepare audio for transcription
                            if len(audio_buffer) == 0:
                                audio_data = np.array([], dtype=np.float32)
                            else:
                                audio_data = np.concatenate(audio_buffer)
                            audio_buffer = []

                            # Convert float32 [-1,1] → int16
                            pcm16 = np.int16(audio_data * 32767)
                            audio_bytes = pcm16.tobytes()

                            # Prepare tensor for model: 1D float32
                            x = torch.from_numpy(audio_data).float().view(1, -1).to(device)
                            with torch.no_grad():
                                z = model(x)

                            if decoder is not None:
                                text = decoder(z[0])
                            else:
                                text = ''

                            # Send event with transcription
                            print(f"VAD: transcribed text={text}")
                            await websocket.send_text(
                                json.dumps(
                                    {
                                        "event": "speech_ended",
                                        "duration": duration,
                                        "text": text,
                                    }
                                )
                            )

                            speech_frames = 0
                            silence_frames = 0

                except WebSocketDisconnect:
                    print("VAD socket disconnected")
                    break
                except Exception as e:
                    print("Error in websocket handler:", e)
                    # continue receiving
                    continue
        finally:
            print("VAD socket closed")



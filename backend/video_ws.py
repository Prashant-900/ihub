import os

# Disable TensorFlow optimization warnings
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'


from fastapi import WebSocket, WebSocketDisconnect
import json
import time
import torch
import torch.nn.functional as F
import base64
import io
import asyncio
from PIL import Image
from load_model import load_emotion_model, detect_emotion

# Global state for tracking current user expression
current_user_expression = None

def register_video(app):
    """Register video streaming WebSocket endpoint with keep-alive support"""
    
    @app.websocket("/ws-video")
    async def websocket_video(websocket: WebSocket):
        global current_user_expression
        
        try:
            await websocket.accept()
        except Exception:
            return
        
        # Load emotion model once per connection
        try:
            model, processor = load_emotion_model()
        except Exception as e:
            try:
                await websocket.send_text(json.dumps({"error": "Failed to load emotion model"}))
            except:
                pass
            await websocket.close()
            return
        
        frame_count = 0
        start_time = time.time()
        last_activity = time.time()
        connection_active = True
        
        # Keep-alive task to monitor connection
        async def keep_alive_monitor():
            nonlocal connection_active, last_activity
            while connection_active:
                try:
                    # Check for inactivity timeout (120 seconds)
                    if time.time() - last_activity > 120:
                        # Send a status message to keep connection alive
                        try:
                            await websocket.send_text(json.dumps({
                                "type": "keep_alive",
                                "status": "Connection active",
                                "uptime": time.time() - start_time
                            }))
                        except Exception:
                            connection_active = False
                            break
                    await asyncio.sleep(10)  # Check every 10 seconds
                except Exception:
                    connection_active = False
                    break
        
        # Start keep-alive monitor task
        monitor_task = asyncio.create_task(keep_alive_monitor())
        
        try:
            while connection_active:
                try:
                    # Use timeout to check for inactivity
                    msg = await asyncio.wait_for(websocket.receive_text(), timeout=60.0)
                    last_activity = time.time()
                    
                except asyncio.TimeoutError:
                    # Timeout but connection still might be valid
                    try:
                        await websocket.send_text(json.dumps({
                            "type": "ping_response",
                            "status": "alive",
                            "frames_received": frame_count
                        }))
                    except Exception:
                        connection_active = False
                        break
                    continue
                
                except WebSocketDisconnect:
                    break
                
                try:
                    payload = json.loads(msg)
                    
                    # Handle ping/keep-alive messages
                    if payload.get("type") == "ping":
                        try:
                            await websocket.send_text(json.dumps({
                                "type": "pong",
                                "status": "alive"
                            }))
                        except Exception:
                            connection_active = False
                            break
                        continue
                    
                    if payload.get("type") == "video_frame":
                        frame_count += 1
                        
                        try:
                            # Decode base64 image
                            image_data = base64.b64decode(payload.get('data', ''))
                            image = Image.open(io.BytesIO(image_data)).convert('RGB')
                            
                            # Run emotion detection on frame
                            if model is not None and processor is not None:
                                try:
                                    result = detect_emotion(image, model, processor)
                                    current_user_expression = result.get('label')
                                    await websocket.send_text(json.dumps({
                                        "status": f"Processing frame {frame_count}",
                                        "emotion": result.get('label'),
                                        "confidence": result.get('confidence'),
                                        "frames_received": frame_count
                                    }))
                                except Exception as e:
                                    try:
                                        await websocket.send_text(json.dumps({
                                            "status": f"Processing frame {frame_count}",
                                            "frames_received": frame_count
                                        }))
                                    except Exception:
                                        connection_active = False
                                        break
                            else:
                                try:
                                    await websocket.send_text(json.dumps({
                                        "status": f"Processing frame {frame_count}",
                                        "frames_received": frame_count
                                    }))
                                except Exception:
                                    connection_active = False
                                    break
                        except Exception as e:
                            # Image processing error - continue
                            pass
                    
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    # Other parsing errors
                    pass
                    
        except Exception as e:
            pass
        finally:
            connection_active = False
            current_user_expression = None
            monitor_task.cancel()
            try:
                await websocket.close()
            except:
                pass

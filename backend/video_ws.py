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
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForImageClassification

# Load emotion model once at module level
emotion_model = None
processor = None

def load_emotion_model():
    """Load the emotion detection model from Hugging Face"""
    global emotion_model, processor
    if emotion_model is None:
        try:
            device = torch.device("cpu")
            model_name = "dima806/facial_emotions_image_detection"
            
            print("🔄 Loading emotion detection model...")
            processor = AutoImageProcessor.from_pretrained(model_name, use_fast=True)
            emotion_model = AutoModelForImageClassification.from_pretrained(model_name)
            emotion_model.eval()
            
            # Quantize for CPU speed-up
            emotion_model = torch.quantization.quantize_dynamic(
                emotion_model, {torch.nn.Linear}, dtype=torch.qint8
            )
            
            print("✅ Emotion model loaded and quantized successfully")
        except Exception as e:
            print(f"❌ Failed to load emotion model: {e}")
            import traceback
            traceback.print_exc()
            return None, None
    return emotion_model, processor

def register_video(app):
    """Register video streaming WebSocket endpoint"""
    
    @app.websocket("/ws-video")
    async def websocket_video(websocket: WebSocket):
        try:
            await websocket.accept()
            print("=" * 60)
            print("🎥 VIDEO WEBSOCKET CONNECTED")
            print("=" * 60)
            
            # Load emotion model
            model, img_processor = load_emotion_model()
            
            frame_count = 0
            start_time = time.time()
        except Exception as e:
            print(f"❌ Failed to accept WebSocket connection: {e}")
            return
        
        try:
            while True:
                try:
                    msg = await websocket.receive_text()
                except WebSocketDisconnect:
                    print("\n" + "=" * 60)
                    print("🎥 VIDEO WEBSOCKET DISCONNECTED BY CLIENT")
                    print("=" * 60)
                    break
                
                try:
                    payload = json.loads(msg)
                    
                    if payload.get("type") == "video_frame":
                        frame_count += 1
                        
                        # Decode base64 image
                        image_data = base64.b64decode(payload.get('data', ''))
                        image = Image.open(io.BytesIO(image_data)).convert('RGB')
                        
                        # Run emotion detection on frame
                        if model is not None and img_processor is not None:
                            try:
                                # Preprocess image using the processor
                                inputs = img_processor(images=image, return_tensors="pt")
                                
                                # Run inference
                                with torch.no_grad():
                                    outputs = model(**inputs)
                                
                                # Get predictions
                                logits = outputs.logits
                                probs = F.softmax(logits, dim=-1)[0]
                                pred_idx = torch.argmax(probs).item()
                                label = model.config.id2label[pred_idx]
                                confidence = probs[pred_idx].item()
                                
                                # Print the emotion detection result
                                print(f"🎭 Frame {frame_count} - Emotion: {label} ({confidence*100:.2f}%)")
                                
                            except Exception as e:
                                print(f"⚠️  Error running emotion model: {e}")
                        
                        # Send acknowledgment back to client
                        await websocket.send_text(json.dumps({
                            "status": f"Processing frame {frame_count}",
                            "frames_received": frame_count
                        }))
                    
                except json.JSONDecodeError as e:
                    print(f"⚠️  Error decoding JSON: {e}")
                    continue
                except Exception as e:
                    print(f"⚠️  Error processing video frame: {e}")
                    continue
                    
        except Exception as e:
            print(f"\n❌ Video WebSocket error: {e}")
        finally:
            total_time = time.time() - start_time
            print("\n" + "=" * 60)
            print("📊 VIDEO SESSION SUMMARY")
            print("=" * 60)
            print(f"   • Total frames processed: {frame_count}")
            print(f"   • Session duration: {total_time:.2f} seconds")
            if total_time > 0:
                print(f"   • Average FPS: {frame_count / total_time:.2f}")
            print("=" * 60 + "\n")

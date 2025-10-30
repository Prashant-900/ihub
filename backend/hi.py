import os
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

import cv2
import torch
from transformers import AutoImageProcessor, AutoModelForImageClassification
import torch.nn.functional as F
from PIL import Image

# 1. Setup model
device = torch.device("cpu")
model_name = "dima806/facial_emotions_image_detection"

print("Loading model...")
processor = AutoImageProcessor.from_pretrained(model_name, use_fast=True)
model = AutoModelForImageClassification.from_pretrained(model_name)
model.eval()

# Quantize for CPU speed-up
model = torch.quantization.quantize_dynamic(model, {torch.nn.Linear}, dtype=torch.qint8)
print("Model loaded and quantized.")

# 2. Webcam setup
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError("Cannot open webcam")

print("Press 'q' to quit.")
frame_count = 0
skip_frames = 100  # run detection every 100 frames (~3-5s depending on webcam FPS)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1
    # Show live feed
    cv2.imshow("Webcam", frame)

    # Run inference occasionally (to avoid lag)
    if frame_count % skip_frames == 0:
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img)
        inputs = processor(images=img_pil, return_tensors="pt")

        with torch.no_grad():
            outputs = model(**inputs)

        logits = outputs.logits
        probs = F.softmax(logits, dim=-1)[0]
        pred_idx = torch.argmax(probs).item()
        label = model.config.id2label[pred_idx]
        conf = probs[pred_idx].item()

        print(f"Detected emotion: {label} ({conf*100:.2f}%)")

    # Quit key
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()

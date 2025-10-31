import torch
import torch.nn.functional as F
from transformers import AutoImageProcessor, AutoModelForImageClassification
from typing import Tuple, Dict, Optional
from PIL.Image import Image

"""
Centralized model loading module for AI character pipeline.

Provides cached loading of STT and emotion detection models to optimize
performance and ensure consistent model usage across the application.
"""

# ============================================
# STT Model Loading
# ============================================
try:
    stt_model, stt_decoder, stt_utils = torch.hub.load(
        repo_or_dir='snakers4/silero-models',
        model='silero_stt',
        language='en',
        device='cpu'
    )
except Exception as e:
    raise RuntimeError(f'Failed to initialize STT model: {e}')


# ============================================
# Emotion Detection Model Loading
# ============================================
_emotion_model_cache = None
_emotion_processor_cache = None


def load_emotion_model() -> Tuple[object, object]:
    """Load emotion detection model from Hugging Face.
    
    Loads the facial emotion detection model with caching to avoid redundant
    downloads and initialization on subsequent calls.
    
    Returns:
        Tuple of (model, processor) for emotion detection
        
    Raises:
        RuntimeError: If model loading fails
    """
    global _emotion_model_cache, _emotion_processor_cache
    
    if _emotion_model_cache is not None:
        return _emotion_model_cache, _emotion_processor_cache
    
    try:
        model_name = "dima806/facial_emotions_image_detection"
        
        # Load processor and model
        processor = AutoImageProcessor.from_pretrained(model_name, use_fast=True)
        model = AutoModelForImageClassification.from_pretrained(model_name)
        model.eval()
        
        # Quantize for CPU performance optimization
        model = torch.quantization.quantize_dynamic(
            model, {torch.nn.Linear}, dtype=torch.qint8
        )
        
        _emotion_model_cache = model
        _emotion_processor_cache = processor
        return model, processor
    except Exception as e:
        raise RuntimeError(f'Failed to load emotion detection model: {e}')


def detect_emotion(
    image: Image,
    model: Optional[object] = None,
    processor: Optional[object] = None
) -> Dict[str, float]:
    """Detect emotion from image.
    
    Performs emotion classification on a facial image, returning the detected
    emotion label and confidence score.
    
    Args:
        image: PIL Image object containing facial image
        model: Emotion detection model (auto-loaded if None)
        processor: Image processor (auto-loaded if None)
        
    Returns:
        Dictionary with keys:
            - 'label': Detected emotion string
            - 'confidence': Confidence score between 0 and 1
            
    Raises:
        RuntimeError: If emotion detection fails
    """
    if model is None or processor is None:
        model, processor = load_emotion_model()
    
    try:
        inputs = processor(images=image, return_tensors="pt")
        
        with torch.no_grad():
            outputs = model(**inputs)
        
        logits = outputs.logits
        probs = F.softmax(logits, dim=-1)[0]
        pred_idx = torch.argmax(probs).item()
        label = model.config.id2label[pred_idx]
        confidence = probs[pred_idx].item()
        
        return {
            'label': label,
            'confidence': confidence
        }
    except Exception as e:
        raise RuntimeError(f'Error detecting emotion: {e}')

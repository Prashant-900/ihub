import React, { useEffect, useRef, useState } from 'react';
import { FiX, FiVideo, FiVideoOff } from 'react-icons/fi';
import { BACKEND_API_WS } from '../constants';

export default function VideoCall({ onClose, onStop, isVisible = true }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [status, setStatus] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentEmotion, setCurrentEmotion] = useState(null);
  const [emotionConfidence, setEmotionConfidence] = useState(0);
  const streamRef = useRef(null);
  const wsRef = useRef(null);
  const intervalRef = useRef(null);

  const startVideoStream = async () => {
    try {
      // Get video stream from user's camera
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'user'
        },
        audio: false
      });

      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }

      // Connect to backend WebSocket
      const wsUrl = `${BACKEND_API_WS}/ws-video`;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.addEventListener('open', () => {
        setStatus('Connected');
        setIsStreaming(true);

        // Start capturing and sending frames
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        
        // Keep-alive ping to prevent connection timeout
        const pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'ping' }));
          }
        }, 25000); // Send ping every 25 seconds
        
        intervalRef.current = setInterval(() => {
          if (videoRef.current && videoRef.current.readyState === videoRef.current.HAVE_ENOUGH_DATA) {
            // Draw video frame to canvas
            canvas.width = videoRef.current.videoWidth || 640;
            canvas.height = videoRef.current.videoHeight || 480;
            ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);

            // Convert canvas to base64 JPEG
            canvas.toBlob((blob) => {
              if (blob && ws.readyState === WebSocket.OPEN) {
                const reader = new FileReader();
                reader.onloadend = () => {
                  const base64data = reader.result.split(',')[1];
                  ws.send(JSON.stringify({
                    type: 'video_frame',
                    data: base64data,
                    timestamp: Date.now(),
                    width: canvas.width,
                    height: canvas.height
                  }));
                };
                reader.readAsDataURL(blob);
              }
            }, 'image/jpeg', 0.7);
          }
        }, 100); // Send ~10 frames per second

        // Store ping interval for cleanup
        ws._pingInterval = pingInterval;
      });

      ws.addEventListener('close', () => {
        setStatus('Disconnected');
        setIsStreaming(false);
        // Clean up ping interval if it exists
        if (ws._pingInterval) clearInterval(ws._pingInterval);
      });

      ws.addEventListener('error', () => {
        setStatus('Connection error');
      });

      ws.addEventListener('message', (ev) => {
        try {
          const msg = JSON.parse(ev.data);
          if (msg.status) {
            setStatus(msg.status);
          }
          if (msg.emotion) {
            setCurrentEmotion(msg.emotion);
            setEmotionConfidence((msg.confidence * 100).toFixed(1));
          }
        } catch {
          // Ignore message parsing errors
        }
      });

    } catch {
      setStatus('Camera access denied');
    }
  };

  const stopVideoStream = () => {
    // Stop interval
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    // Close WebSocket
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    // Stop video tracks
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setIsStreaming(false);
    setStatus('Stopped');
  };

  useEffect(() => {
    // Start video stream when component mounts
    startVideoStream();

    // Cleanup on unmount - only stop if explicitly unmounted
    return () => {
      stopVideoStream();
    };
  }, []);

  const handleStopVideo = () => {
    stopVideoStream();
    onStop && onStop();
  };

  return (
    <div className={`fixed left-1/2 transform -translate-x-1/2 bottom-20 z-50 w-full max-w-4xl px-4 ${!isVisible ? 'hidden' : ''}`}>
      <div className="bg-black/40 backdrop-blur-md border border-white/10 rounded-lg shadow-lg overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between bg-white/5 px-4 py-3 border-b border-white/10">
          <div className="flex items-center gap-2">
            <FiVideo className="w-5 h-5 text-white" />
            <span className="text-white font-medium">Video Stream & Expression</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-white/80">{status}</span>
            <button
              onClick={onClose}
              className="text-white p-2 rounded-md hover:bg-white/10 transition-colors"
              aria-label="Close"
              title="Hide panel (stream continues)"
            >
              <FiX className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Video Preview and Expression Display */}
        <div className="relative bg-black/60 flex items-center justify-center" style={{ height: '360px' }}>
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="w-full h-full object-contain"
          />
          {!isStreaming && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-white/60 text-center">
                <FiVideoOff className="w-16 h-16 mx-auto mb-2" />
                <p>Camera not active</p>
              </div>
            </div>
          )}
          {/* Expression Badge */}
          {isStreaming && currentEmotion && (
            <div className="absolute top-4 right-4 bg-white/10 backdrop-blur-sm border border-white/20 rounded-lg px-4 py-2">
              <div className="text-xs text-white/70">Current Expression</div>
              <div className="text-sm font-semibold text-white">{currentEmotion}</div>
              <div className="text-xs text-white/60">{emotionConfidence}% confidence</div>
            </div>
          )}
        </div>

        {/* Hidden canvas for frame capture */}
        <canvas ref={canvasRef} className="hidden" />

        {/* Controls */}
        <div className="flex items-center justify-center gap-4 px-4 py-4 bg-white/5">
          {isStreaming && (
            <button
              onClick={handleStopVideo}
              className="flex items-center gap-2 px-6 py-3 bg-red-500/80 hover:bg-red-500 text-white rounded-lg transition-colors font-medium"
              title="Stop video stream completely"
            >
              <FiVideoOff className="w-5 h-5" />
              Stop Video
            </button>
          )}
          {!isStreaming && (
            <button
              onClick={startVideoStream}
              className="flex items-center gap-2 px-6 py-3 bg-blue-500/80 hover:bg-blue-500 text-white rounded-lg transition-colors font-medium"
            >
              <FiVideo className="w-5 h-5" />
              Start Video
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

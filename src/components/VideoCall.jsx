import React, { useEffect, useRef, useState } from 'react';
import { FiX, FiVideo, FiVideoOff } from 'react-icons/fi';
import { BACKEND_API_WS } from '../constants';

export default function VideoCall({ onClose }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [status, setStatus] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
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
        console.log('Video WebSocket connected');
        setStatus('Connected');
        setIsStreaming(true);

        // Start capturing and sending frames
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        
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
      });

      ws.addEventListener('close', () => {
        console.log('Video WebSocket closed');
        setStatus('Disconnected');
        setIsStreaming(false);
      });

      ws.addEventListener('error', (e) => {
        console.warn('Video WebSocket error', e);
        setStatus('Connection error');
      });

      ws.addEventListener('message', (ev) => {
        try {
          const msg = JSON.parse(ev.data);
          console.log('Video WS message:', msg);
          if (msg.status) {
            setStatus(msg.status);
          }
        } catch (err) {
          console.warn('Error parsing video message', err);
        }
      });

    } catch (err) {
      console.error('Error starting video stream:', err);
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
    return () => {
      stopVideoStream();
    };
  }, []);

  const handleClose = () => {
    stopVideoStream();
    onClose();
  };

  return (
    <div className="fixed left-1/2 transform -translate-x-1/2 bottom-20 z-50 w-full max-w-4xl px-4">
      <div className="bg-black/40 backdrop-blur-md border border-white/10 rounded-lg shadow-lg overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between bg-white/5 px-4 py-3 border-b border-white/10">
          <div className="flex items-center gap-2">
            <FiVideo className="w-5 h-5 text-white" />
            <span className="text-white font-medium">Video Call</span>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-white/80">{status}</span>
            <button
              onClick={handleClose}
              className="text-white p-2 rounded-md hover:bg-white/10 transition-colors"
              aria-label="Close"
            >
              <FiX className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Video Preview */}
        <div className="relative bg-black/60 flex items-center justify-center" style={{ height: '360px' }}>
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="w-full h-full object-contain rounded-md"
          />
          {!isStreaming && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-white/60 text-center">
                <FiVideoOff className="w-16 h-16 mx-auto mb-2" />
                <p>Camera not active</p>
              </div>
            </div>
          )}
        </div>

        {/* Hidden canvas for frame capture */}
        <canvas ref={canvasRef} className="hidden" />

        {/* Controls */}
        <div className="flex items-center justify-center gap-4 px-4 py-4 bg-white/5">
          {!isStreaming ? (
            <button
              onClick={startVideoStream}
              className="flex items-center gap-2 px-6 py-3 bg-blue-500/80 hover:bg-blue-500 text-white rounded-lg transition-colors font-medium"
            >
              <FiVideo className="w-5 h-5" />
              Start Video
            </button>
          ) : (
            <button
              onClick={stopVideoStream}
              className="flex items-center gap-2 px-6 py-3 bg-red-500/80 hover:bg-red-500 text-white rounded-lg transition-colors font-medium"
            >
              <FiVideoOff className="w-5 h-5" />
              Stop Video
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

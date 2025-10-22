import React, { useEffect, useRef, useState } from 'react';
import { FiX } from 'react-icons/fi';

export default function VoiceVisualizer({ onClose }) {
  const canvasRef = useRef(null);
  const [status, setStatus] = useState('');

  useEffect(() => {
    let audioCtx;
    let analyser;
    let source;
    let rafId;
    let stream;

    // VAD state
    let speaking = false;
    let speechStart = 0;
    let silenceCounter = 0;

    const start = async () => {
      try {
        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        source = audioCtx.createMediaStreamSource(stream);
        analyser = audioCtx.createAnalyser();
        analyser.fftSize = 2048;
        source.connect(analyser);

        const bufferLen = analyser.fftSize;
        const data = new Float32Array(bufferLen);

        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');

  // const sampleRate = audioCtx.sampleRate;

        // Attempt to load webrtcvad; if not available, we'll fallback
        let VAD = null;
        try {
          const mod = await import('webrtcvad');
          VAD = mod && (mod.default || mod);
          // Note: browser support may vary; if VAD API is different, we'll fallback
        } catch (err) {
          console.warn('VAD load failed, using RMS fallback', err);
          VAD = null;
        }

        const draw = () => {
          analyser.getFloatTimeDomainData(data);

          // draw waveform
          ctx.fillStyle = 'rgba(0,0,0,0)';
          ctx.clearRect(0, 0, canvas.width, canvas.height);
          ctx.lineWidth = 2;
          ctx.strokeStyle = '#60A5FA';
          ctx.beginPath();
          const sliceWidth = (canvas.width * 1.0) / bufferLen;
          let x = 0;
          for (let i = 0; i < bufferLen; i++) {
            const v = data[i] * 0.5 + 0.5;
            const y = v * canvas.height;
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
            x += sliceWidth;
          }
          ctx.stroke();

          // compute RMS
          let sum = 0;
          for (let i = 0; i < data.length; i++) sum += data[i] * data[i];
          const rms = Math.sqrt(sum / data.length);

          // VAD detection: attempt to use VAD if available, otherwise RMS threshold
          let isSpeech = false;
          if (VAD && typeof VAD === 'function') {
            // webrtcvad usage in browser may not be supported; skip using it here
            isSpeech = rms > 0.01; // fallback threshold
          } else {
            // simple amplitude-based VAD
            isSpeech = rms > 0.02; // tuned threshold
          }

          if (isSpeech) {
            silenceCounter = 0;
            if (!speaking) {
              speaking = true;
              speechStart = performance.now();
              setStatus('Speech started');
            }
          } else {
            if (speaking) {
              silenceCounter++;
              // consider speech ended after ~300ms of silence (assuming 60fps -> ~18 frames)
              if (silenceCounter > 18) {
                speaking = false;
                const durationMs = performance.now() - speechStart;
                console.log('Speech duration (ms):', durationMs);
                setStatus('Speech ended: ' + (Math.round(durationMs) + ' ms'));
                silenceCounter = 0;
              }
            }
          }

          rafId = requestAnimationFrame(draw);
        };

        draw();
      } catch (err) {
        console.error('VoiceVisualizer error', err);
        setStatus('Microphone access denied');
      }
    };

    start();

    // capture references for cleanup
    const _stream = stream;
    const _audioCtx = audioCtx;
    const _rafId = rafId;
    return () => {
      if (_rafId) cancelAnimationFrame(_rafId);
      try {
        if (_stream) _stream.getTracks().forEach((t) => t.stop());
      } catch (err) {
        console.warn('Error stopping stream tracks', err);
      }
      try {
        if (_audioCtx) _audioCtx.close();
      } catch (err) {
        console.warn('Error closing audio context', err);
      }
    };
  }, []);

  return (
    <div className="fixed left-1/2 transform -translate-x-1/2 bottom-20 z-50 w-full max-w-4xl px-4">
      <div className="flex items-center bg-black/40 backdrop-blur-md border border-white/10 rounded-lg shadow-lg px-3 py-3">
        <button onClick={onClose} className="mr-3 text-white p-2 rounded-md hover:bg-white/10"><FiX className="w-5 h-5"/></button>
        <canvas ref={canvasRef} width={800} height={100} className="flex-1 rounded-md" />
        <div className="ml-3 text-xs text-white/80">{status}</div>
      </div>
    </div>
  );
}

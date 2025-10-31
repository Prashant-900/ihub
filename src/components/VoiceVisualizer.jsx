import React, { useEffect, useRef, useState } from 'react';
import { FiX } from 'react-icons/fi';
import { BACKEND_API_WS } from '../constants';
import { executeAnimationTimeline } from '../api_unity/anim_controller';
import { ClearText } from '../api_unity/index';

export default function VoiceVisualizer({ onClose, pipelineClient }) {
  const canvasRef = useRef(null);
  const [status, setStatus] = useState('');
  const startedRef = useRef(false);
  const cleanupRef = useRef(null);

  useEffect(() => {
    if (startedRef.current) return;
    startedRef.current = true;
    const pipelineClientRef = { current: pipelineClient };

  let audioCtx;
    let analyser;
    let source;
    let rafId;
    let stream;
    let scriptNode;
    let sendInterval;
    let wsVad;
    let pipelineOffRef = { current: null };

    const toBase64Int16 = (int16Arr) => {
      const uint8 = new Uint8Array(int16Arr.buffer);
      let CHUNK = 0x8000;
      let binary = '';
      for (let i = 0; i < uint8.length; i += CHUNK) {
        binary += String.fromCharCode.apply(null, Array.from(uint8.subarray(i, i + CHUNK)));
      }
      return btoa(binary);
    };

    const downsampleBuffer = (buffer, sampleRate, outSampleRate) => {
      if (outSampleRate === sampleRate) return buffer;
      const sampleRateRatio = sampleRate / outSampleRate;
      const newLength = Math.round(buffer.length / sampleRateRatio);
      const result = new Float32Array(newLength);
      let offsetResult = 0;
      let offsetBuffer = 0;
      while (offsetResult < result.length) {
        const nextOffsetBuffer = Math.round((offsetResult + 1) * sampleRateRatio);
        // use average value between the two offsets
        let accum = 0, count = 0;
        for (let i = offsetBuffer; i < nextOffsetBuffer && i < buffer.length; i++) {
          accum += buffer[i];
          count++;
        }
        result[offsetResult] = count ? accum / count : 0;
        offsetResult++;
        offsetBuffer = nextOffsetBuffer;
      }
      return result;
    };

  // VAD state handled by server; local visualization only

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

          // No local VAD here; server will emit speech start/end events

          rafId = requestAnimationFrame(draw);
        };

        // setup ScriptProcessor to capture audio for streaming
        const spBufferSize = 4096;
        scriptNode = audioCtx.createScriptProcessor(spBufferSize, 1, 1);
        const captureBuffer = [];
        scriptNode.onaudioprocess = (evt) => {
          const input = evt.inputBuffer.getChannelData(0);
          // copy to captureBuffer
          captureBuffer.push(new Float32Array(input));
        };
        source.connect(scriptNode);
        scriptNode.connect(audioCtx.destination);

        // If a pipelineClient (WSClient) is provided use it for message I/O
        if (pipelineClientRef.current) {
          try {
            pipelineOffRef.current = pipelineClientRef.current.onMessage((msg) => {
              let data = msg;
              try { data = JSON.parse(msg); } catch { /* ignore parse errors */ }
              if (data && data.event === 'speech_started') setStatus('Speech started');
              if (data && data.event === 'speech_ended') {
                setStatus('Speech ended: ' + Math.round((data.duration || 0) * 1000) + ' ms');
                if (data.timeline) {
                  executeAnimationTimeline(data.timeline).catch(() => {});
                }
              }
              if (data && data.event === 'ai_response') {
                setStatus('Assistant response received');
                if (data.timeline) {
                  executeAnimationTimeline(data.timeline).catch(() => {});
                }
              }
            });
          } catch {
            // Failed to attach message listener
          }
        } else {
          // connect to backend ws-vad directly
          const wsUrl = `${BACKEND_API_WS}/ws-vad`;
          try {
            wsVad = new WebSocket(wsUrl);
            wsVad.addEventListener('open', () => {
              // WebSocket connected
            });
            wsVad.addEventListener('close', () => {
              // WebSocket closed
            });
            wsVad.addEventListener('error', () => {
              // WebSocket error
            });
            wsVad.addEventListener('message', (ev) => {
              try {
                const msg = JSON.parse(ev.data);
                if (msg && msg.event === 'speech_started') {
                  setStatus('Speech started');
                  ClearText();
                }
                if (msg && msg.event === 'speech_ended') {
                  setStatus('Speech ended: ' + Math.round((msg.duration || 0) * 1000) + ' ms');
                  if (msg.timeline) {
                    executeAnimationTimeline(msg.timeline).catch(() => {});
                  }
                }
                if (msg && msg.event === 'ai_response') {
                  setStatus('Assistant response received');
                  if (msg.timeline) {
                    executeAnimationTimeline(msg.timeline).catch(() => {});
                  }
                }
              } catch {
                // Ignore message processing errors
              }
            });
          } catch {
            wsVad = null;
          }
        }

        // periodically send collected audio (every 200ms)
        sendInterval = setInterval(() => {
          if (!captureBuffer.length) return;
          // concat buffers
          let totalLen = 0;
          for (let b of captureBuffer) totalLen += b.length;
          const merged = new Float32Array(totalLen);
          let offset = 0;
          for (let b of captureBuffer) {
            merged.set(b, offset);
            offset += b.length;
          }
          captureBuffer.length = 0;

          // downsample to 16000
          const outRate = 16000;
          const sampleRate = audioCtx.sampleRate;
          const down = downsampleBuffer(merged, sampleRate, outRate);

          // convert to int16
          const int16 = new Int16Array(down.length);
          for (let i = 0; i < down.length; i++) {
            let s = Math.max(-1, Math.min(1, down[i]));
            int16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
          }

          const b64 = toBase64Int16(int16);
          // Prefer pipelineClient for sending audio if available
          if (pipelineClient) {
            try {
              pipelineClientRef.current.send(JSON.stringify({ type: 'audio', sampleRate: outRate, data: b64 }));
            } catch {
              // fallthrough - try raw ws
              if (wsVad && wsVad.readyState === WebSocket.OPEN) {
                wsVad.send(JSON.stringify({ type: 'audio', sampleRate: outRate, data: b64 }));
              }
            }
          } else {
            if (wsVad && wsVad.readyState === WebSocket.OPEN) {
              wsVad.send(JSON.stringify({ type: 'audio', sampleRate: outRate, data: b64 }));
            }
          }
        }, 60);

        draw();
      } catch {
        setStatus('Microphone access denied');
      }
    };

  start();

    const cleanup = () => {
      startedRef.current = false;
      if (rafId) cancelAnimationFrame(rafId);
      try {
        if (scriptNode) {
          scriptNode.disconnect();
          scriptNode.onaudioprocess = null;
        }
      } catch {
        // Ignore script node cleanup errors
      }
      try {
        if (sendInterval) clearInterval(sendInterval);
      } catch {
        // Ignore interval cleanup errors
      }
      try {
        if (wsVad) {
          wsVad.close();
        }
      } catch {
        // Ignore websocket cleanup errors
      }
      try {
        if (stream) stream.getTracks().forEach((t) => t.stop());
      } catch {
        // Ignore stream cleanup errors
      }
      try {
        if (audioCtx) audioCtx.close();
      } catch {
        // Ignore audio context cleanup errors
      }
    };

    cleanupRef.current = cleanup;
    return () => {
      try {
        if (pipelineOffRef.current) pipelineOffRef.current();
  } catch { /* ignore cleanup errors */ }
      cleanup();
    };
  }, [pipelineClient]);

  return (
    <div className="fixed left-1/2 transform -translate-x-1/2 bottom-20 z-50 w-full max-w-4xl px-4">
      <div className="flex items-center bg-black/40 backdrop-blur-md border border-white/10 rounded-lg shadow-lg px-3 py-3">
        <button onClick={() => {
          if (cleanupRef.current) cleanupRef.current();
          onClose();
        }} className="mr-3 text-white p-2 rounded-md hover:bg-white/10"><FiX className="w-5 h-5"/></button>
        <canvas ref={canvasRef} width={800} height={100} className="flex-1 rounded-md" />
        <div className="ml-3 text-xs text-white/80">{status}</div>
      </div>
    </div>
  );
}

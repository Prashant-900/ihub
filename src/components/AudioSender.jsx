import React, { useState } from "react";

// Convert Float32Array to regular array and send to Unity as JSON
function sendAudioToUnity(samples, sampleRate) {
  const unity = window.__unityBgInstance || window.unityInstance || window.Unity;
  if (!unity || typeof unity.SendMessage !== "function") {
    console.warn("Unity instance not ready");
    return;
  }

  // Unity expects two arguments: float[] and sampleRate
  // We'll wrap them in an object and send as JSON string
  const data = {
    samples: Array.from(samples), // convert Float32Array to regular array
    sampleRate: sampleRate
  };

  unity.SendMessage(
    "WebGLInputManagerGameObject", // the GameObject name
    "PlayAudioFromJS",             // the method name
    JSON.stringify(data)           // JSON string argument
  );
  console.log("Sent audio to Unity:", data);
}

export default function AudioSender() {
  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("");

  const handleSend = async () => {
    if (!file) {
      setStatus("No file selected");
      return;
    }
    setStatus("Decoding audio...");
    try {
      // Create or reuse audio context
      const audioCtx =
        window.__unityAudioContext ||
        new (window.AudioContext || window.webkitAudioContext)();

      // Decode audio
      const arrayBuffer = await file.arrayBuffer();
      const decoded = await audioCtx.decodeAudioData(arrayBuffer);

      const samples = decoded.getChannelData(0); // use first channel (mono)
      const sampleRate = decoded.sampleRate;

      // Resume context if suspended
      if (audioCtx.state === "suspended") {
        await audioCtx.resume();
      }

      // Send to Unity (raw samples + sampleRate as JSON)
      sendAudioToUnity(samples, sampleRate);
      setStatus("Audio sent to Unity! Playing locally for volume analysis...");

      // --- Playback locally muted for volume analysis ---
      const source = audioCtx.createBufferSource();
      source.buffer = decoded;

      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 2048;
      const dataArray = new Float32Array(analyser.fftSize);

      const gain = audioCtx.createGain();
      gain.gain.value = 0; // mute local playback

      source.connect(analyser);
      analyser.connect(gain);
      gain.connect(audioCtx.destination);

      let rafId = null;

      const sendVolumeToUnity = (audioBuffer) => {
        let sum = 0;
        for (let i = 0; i < audioBuffer.length; i++) sum += audioBuffer[i] * audioBuffer[i];
        const rms = Math.sqrt(sum / audioBuffer.length);
        const volume = Math.min(1, rms * 5);

        const u = window.__unityBgInstance || window.Unity || window.unityInstance;
        if (u && typeof u.SendMessage === 'function') {
          try {
            u.SendMessage('Epsilon', 'UpdateMouthVolume', volume.toString());
          } catch (sendErr) {
            console.warn('Failed to send volume to Unity', sendErr);
          }
        }
      };

      const tick = () => {
        analyser.getFloatTimeDomainData(dataArray);
        sendVolumeToUnity(dataArray);
        rafId = requestAnimationFrame(tick);
      };

      source.start();
      tick();

      source.onended = () => {
        if (rafId) cancelAnimationFrame(rafId);
        try { source.disconnect(); } catch (e) { console.warn(e); }
        try { analyser.disconnect(); } catch (e) { console.warn(e); }
        try { gain.disconnect(); } catch (e) { console.warn(e); }
        setStatus('Playback finished');
      };
    } catch (err) {
      console.error(err);
      setStatus("Failed to decode/send audio");
    }
  };

  return (
    <div className="mt-2">
      <input
        type="file"
        accept="audio/*"
        onChange={(e) => setFile(e.target.files?.[0] || null)}
      />
      <button
        className="bg-indigo-600 text-white px-3 py-1 rounded ml-2"
        onClick={handleSend}
      >
        Send Audio
      </button>
      <div className="text-xs text-gray-600 mt-1">{status}</div>
    </div>
  );
}

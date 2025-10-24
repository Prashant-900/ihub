import { sendAudioBuffer, playVoice, updateMouthVolume, waitForUnityReady } from '../api_unity/index';

export async function playBlobWithUnity(blob, opts = {}) {
  const { latencyMs = 120, frameMs = 50, maxAttempts = 4 } = opts;

  const AudioCtx = window.AudioContext || window.webkitAudioContext;
  const audioCtx = new AudioCtx();
  window.__globalAudioContext = audioCtx;

  const arrayBuffer = await blob.arrayBuffer();

  // Try to decode audio
  let decoded;
  try {
    decoded = await audioCtx.decodeAudioData(arrayBuffer.slice(0));
  } catch {
    try {
      decoded = await new Promise((resolve, reject) => {
        audioCtx.decodeAudioData(arrayBuffer.slice(0), resolve, reject);
      });
    } catch {
      // Create a minimal dummy decoded object so we can still update mouth
      decoded = {
        duration: 0.5,
        sampleRate: audioCtx.sampleRate,
        getChannelData: () => new Float32Array(100),
      };
    }
  }

  const samples = decoded.getChannelData(0);
  const sr = decoded.sampleRate;

  // compute simple RMS envelope
  const frameSize = Math.max(1, Math.floor(sr * (frameMs / 1000)));
  const envelope = [];
  let maxRms = 0;
  for (let i = 0; i < samples.length; i += frameSize) {
    let sum = 0;
    const end = Math.min(i + frameSize, samples.length);
    for (let j = i; j < end; j++) sum += samples[j] * samples[j];
    const rms = Math.sqrt(sum / (end - i));
    envelope.push(rms);
    if (rms > maxRms) maxRms = rms;
  }
  const norm = envelope.map((v) => (maxRms > 0 ? v / maxRms : 0));

  const plannedStart = audioCtx.currentTime + Math.max(0, latencyMs) / 1000;

  // Wait for Unity
  await waitForUnityReady(5000);

  // Send with retries
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      const res = sendAudioBuffer(samples, sr);
      if (res) {
        break;
      }
    } catch {
      void 0;
    }
    await new Promise((r) => setTimeout(r, 150 * attempt));
  }

  // schedule playVoice
  const now = audioCtx.currentTime;
  const delayMs = Math.max(0, (plannedStart - now) * 1000);
  setTimeout(() => {
    try { playVoice(); } catch { void 0; }
  }, delayMs);

  // schedule mouth updates
  for (let idx = 0; idx < norm.length; idx++) {
    const offsetMs = idx * frameMs;
    const scaled = Math.round(Math.min(1, Math.max(0, norm[idx])) * 100) / 100;
    const whenMs = delayMs + offsetMs;
    setTimeout(() => {
      try { updateMouthVolume(scaled); } catch {
        // silent
      }
    }, whenMs);
  }

  return { plannedStart, duration: decoded.duration, envelope: norm };
}

export default {
  playBlobWithUnity,
};

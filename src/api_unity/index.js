// Centralized Unity API wrapper
const getUnity = () => window.__unityBgInstance || window.unityInstance || window.Unity;

function sendMessage(gameObject, method, param) {
  const u = getUnity();
  if (u && typeof u.SendMessage === 'function') {
    try {
      u.SendMessage(gameObject, method, param);
      return true;
    } catch {
      return false;
    }
  }
  return false;
}

export function sendTrigger(triggerName, speed = 1.0) {
  try {
    const jsonData = JSON.stringify({
      name: triggerName,
      speed: Math.max(0.1, Math.min(2.0, speed))
    });
    return sendMessage("Epsilon", 'TriggerByName', jsonData);
  } catch {
    return false;
  }
}

export function playVoice() {
  return sendMessage("WebGLInputManagerGameObject", 'PlayVoiceFromJS');
}

// Helper to check if Unity SendMessage is available
export function isUnityReady() {
  const u = getUnity();
  return !!(u && typeof u.SendMessage === 'function');
}

// Wait for Unity to become ready, up to timeoutMs (resolves true if ready, false if timed out)
export async function waitForUnityReady(timeoutMs = 3000) {
  const start = Date.now();
  if (isUnityReady()) return true;
  return new Promise((resolve) => {
    const interval = setInterval(() => {
      if (isUnityReady()) {
        clearInterval(interval);
        resolve(true);
      } else if (Date.now() - start > timeoutMs) {
        clearInterval(interval);
        resolve(false);
      }
    }, 150);
  });
}

export function sendAudioJSON(jsonStr) {
  // expects jsonStr containing samples array and sampleRate
  return sendMessage('WebGLInputManagerGameObject', 'PlayAudioFromJS', jsonStr);
}

// Decode a File or ArrayBuffer and send audio samples to Unity
export async function sendAudioFile(file) {
  try {
    const arrayBuffer = await file.arrayBuffer();
    const AudioCtx = window.__unityAudioContext || (window.AudioContext || window.webkitAudioContext);
    const audioCtx = window.__unityAudioContext || new AudioCtx();
    window.__unityAudioContext = audioCtx;
    let decoded;
    try {
      decoded = await audioCtx.decodeAudioData(arrayBuffer.slice(0));
    } catch {
      try {
        decoded = await new Promise((resolve, reject) => {
          audioCtx.decodeAudioData(arrayBuffer.slice(0), resolve, (e) => reject(e));
        });
      } catch {
        throw new Error('Audio decode failed');
      }
    }
    const samples = decoded.getChannelData(0);
    const data = {
      samples: Array.from(samples),
      sampleRate: decoded.sampleRate,
    };
    return sendAudioJSON(JSON.stringify(data));
  } catch {
    return false;
  }
}

export function sendAudioBuffer(samples, sampleRate) {
  try {
    const data = { samples: Array.from(samples), sampleRate };
    return sendAudioJSON(JSON.stringify(data));
  } catch {
    return false;
  }
}

export function updateMouthVolume(volume) {
  return sendMessage("Epsilon", 'UpdateMouthVolume', volume.toString());
}

export function changeExpression(intVal) {
  return sendMessage("Epsilon", 'ChangeExpression', intVal.toString());
}

export function setBackground(spriteName) {
  if (!spriteName) return false;
  return sendMessage("bg", 'SetBackground', spriteName);
}

export function ClearText() {
  return sendMessage("text", 'ClearAllTextBoxes', '');
}

export function setTextBox(text, duration, position, type) {
  try {
    const jsonData = JSON.stringify({
      text: text || '',
      position: position || 0,
      type: type || 0,
      duration: duration || 2.0
    });
    return sendMessage("text", 'ShowTextBox', jsonData);
  } catch {
    return false;
  }
}

export default {
  sendTrigger,
  playVoice,
  sendAudioBuffer,
  sendAudioFile,
  sendAudioJSON,
  updateMouthVolume,
  changeExpression,
  setBackground,
  setTextBox,
  isUnityReady,
  waitForUnityReady,
};

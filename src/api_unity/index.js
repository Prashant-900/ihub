// Centralized Unity API wrapper
const getUnity = () => window.__unityBgInstance || window.unityInstance || window.Unity;

function sendMessage(gameObject, method, param) {
  const u = getUnity();
  if (u && typeof u.SendMessage === 'function') {
    try {
      u.SendMessage(gameObject, method, param);
      return true;
    } catch (e) {
      console.error('SendMessage error', e);
      return false;
    }
  }
  console.warn('Unity not ready for SendMessage');
  return false;
}

export function sendTrigger(triggerName, speed = 1.0) {
  try {
    const jsonData = JSON.stringify({
      name: triggerName,
      speed: Math.max(0.1, Math.min(2.0, speed))
    });
    return sendMessage("Epsilon", 'TriggerByName', jsonData);
  } catch (e) {
    console.error('sendTrigger failed', e);
    return false;
  }
}

export function playVoice() {
  return sendMessage("WebGLInputManagerGameObject", 'PlayVoiceFromJS');
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
    const decoded = await audioCtx.decodeAudioData(arrayBuffer);
    const samples = decoded.getChannelData(0);
    const data = {
      samples: Array.from(samples),
      sampleRate: decoded.sampleRate,
    };
    return sendAudioJSON(JSON.stringify(data));
  } catch (e) {
    console.error('sendAudioFile failed', e);
    return false;
  }
}

export function sendAudioBuffer(samples, sampleRate) {
  try {
    const data = { samples: Array.from(samples), sampleRate };
    return sendAudioJSON(JSON.stringify(data));
  } catch (e) {
    console.error('sendAudioBuffer failed', e);
    return false;
  }
}

export function updateMouthVolume(volume) {
  return sendMessage("WebGLInputManagerGameObject", 'UpdateMouthVolume', volume.toString());
}

export function changeExpression(intVal) {
  return sendMessage("Epsilon", 'ChangeExpression', intVal.toString());
}

export function setBackground(spriteName) {
  if (!spriteName) return false;
  return sendMessage("bg", 'SetBackground', spriteName);
}



export default {
  sendTrigger,
  playVoice,
  sendAudioJSON,
  updateMouthVolume,
  changeExpression,
  setBackground
};

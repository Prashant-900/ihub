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

export function sendTrigger(gameObject, triggerName) {
  return sendMessage(gameObject, 'TriggerByName', triggerName);
}

export function playVoice(gameObject = 'WebGLInputManagerGameObject') {
  return sendMessage(gameObject, 'PlayVoiceFromJS');
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

export function updateMouthVolume(gameObject = 'WebGLInputManager', volume) {
  return sendMessage(gameObject, 'UpdateMouthVolume', volume.toString());
}

export function changeExpression(gameObject, intVal) {
  return sendMessage(gameObject, 'ChangeExpression', intVal.toString());
}

export function setBackground(spriteName, gameObject = 'bg') {
  if (!spriteName) return false;
  return sendMessage(gameObject, 'SetBackground', spriteName);
}

export default {
  sendTrigger,
  playVoice,
  sendAudioJSON,
  updateMouthVolume,
  changeExpression,
  setBackground,
};

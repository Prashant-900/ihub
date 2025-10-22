// Resume/create a shared AudioContext for Unity WebGL so browsers allow audio playback
window.resumeUnityAudioContext = () => {
  try {
    if (typeof AudioContext !== 'undefined' || typeof window.webkitAudioContext !== 'undefined') {
      if (!window.__unityAudioContext) {
        window.__unityAudioContext = new (window.AudioContext || window.webkitAudioContext)();
      }
      if (window.__unityAudioContext.state === 'suspended') {
        window.__unityAudioContext.resume().then(() => {
          console.log('[WebGLAudio] AudioContext resumed');
        }).catch((e) => console.warn('[WebGLAudio] resume failed', e));
      }
    }
  } catch (e) {
    console.warn('[WebGLAudio] Error resuming audio context', e);
  }
};

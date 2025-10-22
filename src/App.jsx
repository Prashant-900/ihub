import React, { useState } from 'react';
import ModelBackground from './components/ModelBackground';
import AudioSender from './components/AudioSender';

function App() {
  const [msg, setMsg] = useState('embarrasedtrigger');

  const sendToUnity = (triggerName) => {
    const inst = window.__unityBgInstance;
    // Replace 'GameObjectName' with the name of the GameObject that has the CharAnim script
    const goName = 'Epsilon';
    const method = 'TriggerByName';
    if (!triggerName) triggerName = msg;

    if (inst && typeof inst.SendMessage === 'function') {
      try {
        inst.SendMessage(goName, method, triggerName);
        console.log('Sent trigger to Unity:', triggerName);
      } catch (e) {
        console.error('SendMessage error', e);
      }
    } else if (window.Unity && typeof window.Unity.SendMessage === 'function') {
      window.Unity.SendMessage(goName, method, triggerName);
    } else {
      console.warn('Unity instance not ready yet');
    }
  };


  return (
    <>
      <ModelBackground />

      {/* Overlay controls: visible and interactable (remove pointer-events-none for this area) */}
  <div className="fixed top-4 left-4 z-50 bg-white/70 dark:bg-white/50 rounded-md p-3 shadow-md backdrop-blur-sm pointer-events-auto">
        <label className="block text-sm font-medium mb-1">Message to Unity</label>
        <div className="flex items-center gap-2">
          <input
            type="text"
            tabIndex={0}
            className="border rounded px-2 py-1 text-sm w-64"
            value={msg}
            onChange={(e) => setMsg(e.target.value)}
            onPointerDown={(e) => { e.stopPropagation(); }}
          />
          <button
            className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
            onClick={() => sendToUnity()}
          >
            Send trigger
          </button>
        </div>
        <div className="text-xs text-gray-600 mt-2">GameObject name (with <code className="font-mono">CharAnim</code> script): <code className="font-mono">JSReceiver</code></div>
        <AudioSender />
      </div>
    </>
  );
}

export default App;

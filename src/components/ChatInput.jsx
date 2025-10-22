import React, { useState } from 'react';
import { FiSend, FiMic } from 'react-icons/fi';
import VoiceVisualizer from './VoiceVisualizer';

export default function ChatInput({ onSend }) {
  const [text, setText] = useState('');
  const [showVisualizer, setShowVisualizer] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (text.trim()) {
      onSend && onSend(text.trim());
      setText('');
    }
  };

  if (showVisualizer) {
    return <VoiceVisualizer onClose={() => setShowVisualizer(false)} />;
  }

  return (
    <div className="fixed left-1/2 transform -translate-x-1/2 bottom-20 z-50 w-full max-w-4xl px-4">
      <form onSubmit={handleSubmit} className="flex items-center bg-white/10 dark:bg-black/20 backdrop-blur-md border border-white/10 dark:border-white/8 rounded-lg shadow-lg px-3 py-3">
        <button type="button" onClick={() => setShowVisualizer(true)} className="p-2 rounded-md text-white/90 hover:bg-white/10" aria-label="audio">
          <FiMic className="h-5 w-5" />
        </button>

        <input
          className="flex-1 bg-transparent px-4 py-3 text-lg text-white placeholder-white/70 outline-none"
          placeholder="Type a message and press Enter"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />

        <button
          type="submit"
          className="ml-2 p-2 rounded-md text-white/90 hover:bg-white/10 flex items-center justify-center"
          aria-label="send"
        >
          <FiSend className="h-5 w-5" />
        </button>
      </form>
    </div>
  );
}

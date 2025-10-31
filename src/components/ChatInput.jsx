import React, { useState, useRef } from 'react';
import { FiSend, FiMic, FiVideo } from 'react-icons/fi';
import VoiceVisualizer from './VoiceVisualizer';
import VideoCall from './VideoCall';
import { ClearText } from '../api_unity/index';

export default function ChatInput({ onSend, pipelineClient }) {
  const [text, setText] = useState('');
  const [showVisualizer, setShowVisualizer] = useState(false);
  const [showVideoCall, setShowVideoCall] = useState(false);
  const [videoStreamActive, setVideoStreamActive] = useState(false);
  const textInputStartedRef = useRef(false);

  const handleTextChange = (e) => {
    const newText = e.target.value;
    // Call ClearText when user starts typing (first character)
    if (!textInputStartedRef.current && newText.length > 0) {
      textInputStartedRef.current = true;
      ClearText();
    }
    // Reset flag when text is cleared
    if (newText.length === 0) {
      textInputStartedRef.current = false;
    }
    setText(newText);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (text.trim()) {
      onSend && onSend(text.trim());
      setText('');
      textInputStartedRef.current = false;
    }
  };

  const handleVideoToggle = () => {
    if (!videoStreamActive) {
      // Starting video stream for the first time
      setVideoStreamActive(true);
      setShowVideoCall(true);
    } else {
      // Video stream is active, just toggle the panel
      setShowVideoCall(!showVideoCall);
    }
  };

  const handleVideoClose = () => {
    // Only hide the panel, keep the stream running
    setShowVideoCall(false);
  };

  const handleStopAllVideo = () => {
    // This will be called from VideoCall when user clicks "Stop Video"
    setVideoStreamActive(false);
    setShowVideoCall(false);
  };

  if (showVisualizer) {
    return <VoiceVisualizer onClose={() => setShowVisualizer(false)} pipelineClient={pipelineClient} />;
  }

  return (
    <>
      {/* Video Call Panel - Only hidden, not unmounted */}
      {videoStreamActive && (
        <VideoCall 
          onClose={handleVideoClose} 
          onStop={handleStopAllVideo}
          isVisible={showVideoCall}
        />
      )}

      {/* Chat Input */}
      <div className="fixed left-1/2 transform -translate-x-1/2 bottom-20 z-50 w-full max-w-4xl px-4">
        <form onSubmit={handleSubmit} className="flex items-center bg-white/10 dark:bg-black/20 backdrop-blur-md border border-white/10 dark:border-white/8 rounded-lg shadow-lg px-3 py-3">
          <button type="button" onClick={() => setShowVisualizer(true)} className="p-2 rounded-md text-white/90 hover:bg-white/10" aria-label="audio">
            <FiMic className="h-5 w-5" />
          </button>

          <button type="button" onClick={handleVideoToggle} className="p-2 rounded-md text-white/90 hover:bg-white/10" aria-label="video call">
            <FiVideo className="h-5 w-5" />
          </button>

          <input
            className="flex-1 bg-transparent px-4 py-3 text-lg text-white placeholder-white/70 outline-none"
            placeholder="Type a message and press Enter"
            value={text}
            onChange={handleTextChange}
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
    </>
  );
}

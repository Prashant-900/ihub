import React, { useEffect, useState, useRef } from 'react';
import { FiPlay, FiVolume2, FiMessageSquare } from 'react-icons/fi';
import { BACKEND_API } from '../constants';

export default function TopChat({ wsClient, responseMode, onResponseModeChange }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  const containerRef = useRef(null);
  const uidRef = useRef(0);
  const makeUid = (prefix = 'm') => {
    uidRef.current += 1;
    return `${prefix}-${Date.now()}-${uidRef.current}`;
  };

  // Fetch conversation history once on mount
  useEffect(() => {
    let mounted = true;
    const fetchHistory = async () => {
      try {
        const res = await fetch(`${BACKEND_API}/admin/conversations`);
        if (!res.ok) throw new Error('fetch failed');
        const data = await res.json();
        if (!mounted) return;
        let list = (data.items || []).map((it, idx) => {
          if (it.type === 'message') return { id: it.id, text: it.text, created_at: it.created_at, _uid: `user-${it.id ?? 'x'}-${it.created_at ?? ''}-${idx}` };
          return { id: it.id, text: it.text, audio_id: it.audio_id, timeline: it.timeline, created_at: it.created_at, _uid: `ai-${it.id ?? 'x'}-${it.created_at ?? ''}-${idx}` };
        });
        // sort oldest -> newest by created_at
        list = list.sort((a,b) => (a.created_at || '') > (b.created_at || '') ? 1 : -1);
        setItems(list);
      } catch {
        void 0;
      } finally {
        if (mounted) setLoading(false);
      }
    };
    fetchHistory();
    return () => { mounted = false; };
  }, []);

  // Listen for live ai_response events and prepend them
  useEffect(() => {
    if (!wsClient) return;
    const off = wsClient.onMessage((msg) => {
      let data = msg;
      try { data = JSON.parse(msg); } catch { void 0; }
      if (data && data.event === 'ai_response') {
        const item = { text: data.response, timeline: data.timeline, audio_id: data.audio_id, created_at: data.created_at || new Date().toISOString(), _uid: makeUid('ai') };
        setItems((s) => [...s, item]);
      }
      if (data && data.event === 'user_message') {
        const item = { text: data.text, created_at: data.created_at || new Date().toISOString(), _uid: makeUid('user') };
        setItems((s) => [...s, item]);
      }
    });
    return () => off();
  }, [wsClient]);

  // Auto-scroll to bottom when items change
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    // small timeout to let DOM paint
    setTimeout(() => {
      el.scrollTop = el.scrollHeight;
    }, 50);
  }, [items]);

  const playAudio = async (audioId) => {
    try {
      const url = `${BACKEND_API}/audio/${encodeURIComponent(audioId)}`;
      const resp = await fetch(url);
      if (!resp.ok) throw new Error('audio fetch failed');
      const arrayBuffer = await resp.arrayBuffer();
      const AudioCtx = window.__globalAudioContext || (window.AudioContext || window.webkitAudioContext);
      const audioCtx = window.__globalAudioContext || new AudioCtx();
      window.__globalAudioContext = audioCtx;
      const decoded = await audioCtx.decodeAudioData(arrayBuffer);
      const src = audioCtx.createBufferSource();
      src.buffer = decoded;
      src.connect(audioCtx.destination);
      // start slightly in future to ensure resume takes effect
      try {
        const when = Math.max(0, audioCtx.currentTime + 0.02);
        src.start(when);
      } catch {
        // fallback to immediate start
        try { src.start(0); } catch { void 0; }
      }
    } catch {
      void 0;
    }
  };

  return (
    <div className="fixed top-6 left-6 z-60 text-sm w-80 bg-white/8 dark:bg-black/30 backdrop-blur-md border border-white/10 p-2 rounded-md">
      <div className="flex items-center justify-between mb-2">
        <div className="font-medium text-white">Conversation</div>
        <button
          onClick={() => onResponseModeChange(responseMode === 'audio' ? 'text' : 'audio')}
          className={`flex items-center gap-1 px-2 py-1 rounded text-xs font-medium transition-colors ${
            responseMode === 'audio'
              ? 'bg-blue-600 text-white'
              : 'bg-green-600 text-white'
          }`}
          title={`Response mode: ${responseMode}`}
        >
          {responseMode === 'audio' ? (
            <>
              <FiVolume2 className="w-3 h-3" />
              <span>Audio</span>
            </>
          ) : (
            <>
              <FiMessageSquare className="w-3 h-3" />
              <span>Text</span>
            </>
          )}
        </button>
      </div>
      <div ref={containerRef} className="flex flex-col gap-2 max-h-64 overflow-auto scrollbar-custom">
        {loading && <div className="text-xs text-white/60">Loading...</div>}
        {items.length === 0 && !loading && <div className="text-xs text-white/60">No messages yet</div>}
  {items.map((it) => {
          // consider it an AI message if it has a timeline or audio_id
          const isAI = !!(it.timeline || it.audio_id);
          // strip trailing ' (ai reply)' if present
          const displayText = typeof it.text === 'string' ? it.text.replace(/\s*\(ai reply\)\s*$/i, '') : it.text;
          const time = it.created_at ? new Date(it.created_at) : null;
          const timeStr = time ? time.toLocaleString() : '';
          return (
            <div key={it._uid} className="bg-white/5 p-2 rounded">
              <div className="flex items-center justify-between mb-1">
                <div className="text-xs text-white/70">{isAI ? 'Assistant' : 'You'}</div>
                <div className="text-xs text-white/50">{timeStr}</div>
              </div>
              <div className="text-white text-sm">{displayText}</div>
              {it.audio_id && (
                <button onClick={() => playAudio(it.audio_id)} className="mt-2 text-xs text-blue-200 flex items-center gap-2">
                  <FiPlay className="w-4 h-4" />
                  <span>Play</span>
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

import React, { useEffect, useRef, useState } from 'react';
import ModelBackground from './components/ModelBackground';
import ChatInput from './components/ChatInput';
import BackgroundPicker from './components/BackgroundPicker';
import TopChat from './components/TopChat';
import WSClient from './ws';
import { BACKEND_API_WS, BACKEND_API } from './constants';
import { executeAnimationTimeline } from './api_unity/anim_controller';
import { playBlobWithUnity } from './utils/audioPipeline';
import { setTextBox, ClearText } from './api_unity/index';

function App() {
  const [pipelineWsClient, setPipelineWsClient] = useState(null);
  const [responseMode, setResponseMode] = useState('audio');
  const pipelineWsRef = useRef(null);

  useEffect(() => {
    const base = BACKEND_API_WS
    const wsUrl = `${base}/ws`;
    const client = new WSClient(wsUrl);
    // store in a ref to avoid including in deps
    const clientRef = { current: client };
    client.connect();
    const off = client.onMessage((m) => {
      // Handle speech_started event broadcast from backend
      let d = m;
      try { d = JSON.parse(m); } catch { /* ignore parse errors */ }
      if (d && d.event === 'speech_started') {
        // Call ClearText globally when voice detection starts
        ClearText();
      }
    });

    // pipeline WS (for text messages to pipeline)
    const pipelineUrl = `${base}/ws-vad`;
    const pipelineClient = new WSClient(pipelineUrl);
    pipelineClient.connect();
    const offPipeline = pipelineClient.onMessage((m) => {
      let d = m;
      try { d = JSON.parse(m); } catch { /* ignore parse errors */ }
      try {
        if (d && d.event === 'ai_response') {
          (async () => {
            let plannedStart;
            // Only fetch and play audio if responseMode is 'audio'
            if (d.responseMode === 'audio' && d.audio_id) {
              const audioUrl = `${BACKEND_API}/audio/${encodeURIComponent(d.audio_id)}`;
              try {
                const resp = await fetch(audioUrl);
                if (resp.ok) {
                  const blob = await resp.blob();
                  const res = await playBlobWithUnity(blob, { latencyMs: 120 });
                  plannedStart = res.plannedStart;
                }
              } catch { /* ignore audio fetch errors */ }
            }
            if (d.timeline) {
              const startAt = typeof plannedStart === 'number' ? plannedStart : undefined;
              executeAnimationTimeline(d.timeline, startAt ? { startAt } : undefined).catch(() => {});
            }
            // Handle text box data - ai_text is now an array of text objects
            if (d.text && Array.isArray(d.text)) {
              d.text.forEach((textItem) => {
                const { sentence, duration, pos, type } = textItem;
                setTextBox(sentence, duration, pos, type);
              });
            }
          })();
        }
      } catch { /* ignore response errors */ }
    });
    pipelineWsRef.current = pipelineClient;
    setPipelineWsClient(pipelineClient);
    return () => {
      off();
      offPipeline();
      if (clientRef.current) clientRef.current.close();
      if (pipelineClient) pipelineClient.close();
    };
  }, []);

  return (
    <>
      <ModelBackground />
      <TopChat wsClient={pipelineWsClient} responseMode={responseMode} onResponseModeChange={setResponseMode} />
      <BackgroundPicker />
      <ChatInput pipelineClient={pipelineWsClient} responseMode={responseMode} onSend={(text) => {
        // send text to pipeline WS as JSON with response mode
        if (pipelineWsRef.current) pipelineWsRef.current.send(JSON.stringify({type: 'text', text, responseMode}));
      }} />
    </>
  );
}

export default App;

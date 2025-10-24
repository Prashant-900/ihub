import React, { useEffect, useRef, useState } from 'react';
import ModelBackground from './components/ModelBackground';
import ChatInput from './components/ChatInput';
import BackgroundPicker from './components/BackgroundPicker';
import TopChat from './components/TopChat';
import WSClient from './ws';
import { BACKEND_API_WS, BACKEND_API } from './constants';
import { executeAnimationTimeline } from './api_unity/anim_controller';
import { playBlobWithUnity } from './utils/audioPipeline';

function App() {
  const [pipelineWsClient, setPipelineWsClient] = useState(null);
  const pipelineWsRef = useRef(null);

  useEffect(() => {
    const base = BACKEND_API_WS
    const wsUrl = `${base}/ws`;
    const client = new WSClient(wsUrl);
    // store in a ref to avoid including in deps
    const clientRef = { current: client };
    client.connect();
    const off = client.onMessage(() => {});

    // pipeline WS (for text messages to pipeline)
    const pipelineUrl = `${base}/ws-vad`;
    const pipelineClient = new WSClient(pipelineUrl);
    pipelineClient.connect();
    // attach a debug listener so we can see incoming pipeline messages
    const offPipeline = pipelineClient.onMessage((m) => {
      let d = m;
      try { d = JSON.parse(m); } catch { void 0; }
      try {
        if (d && d.event === 'ai_response') {
          (async () => {
            let plannedStart;
            if (d.audio_id) {
              const audioUrl = `${BACKEND_API}/audio/${encodeURIComponent(d.audio_id)}`;
              try {
                const resp = await fetch(audioUrl);
                if (resp.ok) {
                  const blob = await resp.blob();
                  const res = await playBlobWithUnity(blob, { latencyMs: 120 });
                  plannedStart = res.plannedStart;
                }
              } catch { void 0; }
            }
            if (d.timeline) {
              const startAt = typeof plannedStart === 'number' ? plannedStart : undefined;
              executeAnimationTimeline(d.timeline, startAt ? { startAt } : undefined).catch(() => {});
            }
          })();
        }
      } catch { void 0; }
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
  <TopChat wsClient={pipelineWsClient} />
      <BackgroundPicker />
      <ChatInput pipelineClient={pipelineWsClient} onSend={(text) => {
        // send text to pipeline WS as JSON
        if (pipelineWsRef.current) pipelineWsRef.current.send(JSON.stringify({type: 'text', text}));
      }} />
    </>
  );
}

export default App;

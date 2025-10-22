import React, { useEffect, useRef } from 'react';
import ModelBackground from './components/ModelBackground';
import ChatInput from './components/ChatInput';
import BackgroundPicker from './components/BackgroundPicker';
import WSClient from './ws';
import { BACKEND_API_WS } from './constants';

function App() {
  const wsRef = useRef(null);

  useEffect(() => {
    const base = BACKEND_API_WS
    const wsUrl = `${base}/ws`;
    const client = new WSClient(wsUrl);
    wsRef.current = client;
    client.connect();
    const off = client.onMessage((msg) => console.log('WS msg:', msg));
    return () => {
      off();
      client.close();
    };
  }, []);

  return (
    <>
      <ModelBackground />
      <BackgroundPicker />
      <ChatInput onSend={(text) => {
        console.log('Send from chat input:', text);
        if (wsRef.current) wsRef.current.send(text);
      }} />
    </>
  );
}

export default App;

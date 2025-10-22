import React from 'react';
import ModelBackground from './components/ModelBackground';
import ChatInput from './components/ChatInput';
import BackgroundPicker from './components/BackgroundPicker';

function App() {


  return (
    <>
      <ModelBackground />
  <BackgroundPicker />
      <ChatInput onSend={(text) => {
        console.log('Send from chat input:', text);
        // temporary: map chat input to trigger for testing
        // sendTrigger('Epsilon', text);
      }} />
    </>
  );
}

export default App;

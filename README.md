# iHub - AI Companion WebGL Integration

An interactive AI companion application built with React + Vite that embeds a Unity WebGL animated character. The companion responds to user interactions with expressive animations, emotion triggers, and real-time lip-sync, creating an engaging virtual assistant experience.

## 🤖 What is This?

This is an **AI companion web application** featuring:
- **Interactive 3D Character** - Unity WebGL character (Epsilon) with emotion-based animations
- **Real-time Communication** - Bidirectional messaging between web UI and Unity runtime
- **Audio Processing** - Upload audio files or stream voice input with automatic lip-sync
- **Emotion Triggers** - Send emotion states (embarrassed, happy, sad, etc.) to animate the character
- **Voice Visualization** - Real-time mouth movement synced to audio volume analysis

Perfect for building virtual assistants, chatbots with visual presence, educational companions, or interactive storytelling experiences.

## 🎯 Features

- ✨ **Full-screen 3D character background** - Seamlessly integrated Unity WebGL build
- 🎭 **Emotion-based animations** - Trigger character expressions and poses
- 🎤 **Audio upload & processing** - Browser-based audio decoding and analysis
- 👄 **Real-time lip-sync** - Mouth movements synced to audio volume (RMS analysis)
- 🔄 **Live communication** - React UI controls Unity character in real-time
- 🎨 **Modern UI** - Tailwind CSS overlay controls with backdrop blur

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│          React App (UI Layer)          │
│  ┌─────────────┐  ┌──────────────────┐ │
│  │   App.jsx   │  │  AudioSender.jsx │ │
│  │  (Triggers) │  │  (Audio + Volume)│ │
│  └──────┬──────┘  └────────┬─────────┘ │
│         │                   │           │
│         └───────┬───────────┘           │
│                 ▼                       │
│      window.__unityBgInstance          │
│         (SendMessage Bridge)           │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│       Unity WebGL Build (Canvas)        │
│  ┌─────────────────────────────────┐   │
│  │  GameObject: "Epsilon"          │   │
│  │  - TriggerByName(string)        │   │
│  │  - UpdateMouthVolume(string)    │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │  GameObject: "WebGLInputManager"│   │
│  │  - PlayAudioFromJS(string json) │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

## 🚀 Getting Started

### Prerequisites

- Node.js 18+ and npm
- Unity WebGL build files in `model/Build/`

### Installation

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Development

The app will be available at `http://localhost:5173` (or the port shown in terminal).

## 📁 Project Structure

```
ihub/
├── src/
│   ├── main.jsx                    # React entry point
│   ├── App.jsx                     # Main app with trigger UI
│   ├── index.css                   # Tailwind imports
│   ├── components/
│   │   ├── ModelBackground.jsx     # Unity WebGL loader & canvas
│   │   └── AudioSender.jsx         # Audio upload & processing
│   └── utils/
│       └── audioPipeline.js        # Audio utilities (if present)
├── model/
│   └── Build/                      # Unity WebGL build files
│       ├── model.loader.js         # Unity loader script
│       ├── model.framework.js      # Unity framework (wasm glue)
│       ├── model.wasm              # WebAssembly binary
│       └── model.data              # Unity asset bundle
├── public/
│   └── webglAudioResume.js         # Audio autoplay policy handler
└── package.json
```

## 🔧 Key Components

### `ModelBackground.jsx`
Loads and initializes the Unity WebGL build:
- Dynamically injects Unity loader script
- Creates Unity instance from canvas
- Exposes instance globally as `window.__unityBgInstance`
- Handles cleanup on unmount

### `App.jsx`
Main UI for sending triggers to Unity:
- Text input for custom trigger names
- Sends messages to Unity GameObject `"Epsilon"` via `TriggerByName(string)` method
- Includes `AudioSender` component

### `AudioSender.jsx`
Audio file processing and streaming:
- Decodes audio files using Web Audio API
- Sends raw audio samples to Unity as JSON
- Computes real-time RMS volume from audio
- Sends volume updates to Unity for mouth animation sync

## 🔌 Unity Integration

### Required Unity GameObjects & Methods

Your Unity scene must have these GameObjects with corresponding methods:

#### GameObject: `"Epsilon"`
```csharp
public class CharAnim : MonoBehaviour
{
    // Receives trigger strings from React
    public void TriggerByName(string triggerName)
    {
        // Handle animation trigger
        Debug.Log($"Received trigger: {triggerName}");
    }
    
    // Receives volume values for lip-sync (sent as string)
    public void UpdateMouthVolume(string volumeStr)
    {
        float volume = float.Parse(volumeStr);
        // Update mouth blend shape or animation parameter
    }
}
```

#### GameObject: `"WebGLInputManagerGameObject"`
```csharp
[System.Serializable]
public class AudioData
{
    public float[] samples;
    public int sampleRate;
}

public class WebGLInputManager : MonoBehaviour
{
    // Receives audio data as JSON string
    public void PlayAudioFromJS(string json)
    {
        AudioData data = JsonUtility.FromJson<AudioData>(json);
        // Process audio samples (data.samples, data.sampleRate)
    }
}
```

## 📡 Communication Flow

### Sending Triggers
```javascript
// From React/JS
window.__unityBgInstance.SendMessage(
    'Epsilon',           // GameObject name
    'TriggerByName',     // Method name
    'embarrassedtrigger' // String parameter
);
```

### Sending Audio
```javascript
// From React/JS
const audioData = {
    samples: Array.from(float32Array),
    sampleRate: 48000
};
window.__unityBgInstance.SendMessage(
    'WebGLInputManagerGameObject',
    'PlayAudioFromJS',
    JSON.stringify(audioData)
);
```

### Sending Volume (Real-time)
```javascript
// From React/JS (called every animation frame)
window.__unityBgInstance.SendMessage(
    'Epsilon',
    'UpdateMouthVolume',
    volume.toString() // 0.0 - 1.0
);
```

## ⚠️ Common Issues & Solutions

### Unity Instance Not Ready
**Problem:** `SendMessage` called before Unity loads  
**Solution:** Check `window.__unityBgInstance` exists before calling

### GameObject Not Found
**Problem:** Messages not reaching Unity  
**Solution:** Verify GameObject names match exactly (case-sensitive)

### Large Audio Files
**Problem:** JSON.stringify of large Float32Arrays is slow  
**Solution:** Chunk audio or send downsampled data

### Audio Not Playing
**Problem:** Browser autoplay policy blocks audio  
**Solution:** Ensure user interaction (click) before creating AudioContext

### CORS / 404 Errors
**Problem:** Unity build files not loading  
**Solution:** Verify files exist in `/model/Build/` and dev server serves them

## 🎨 Tech Stack

- **React 19** - UI framework
- **Vite 7** - Build tool and dev server
- **Tailwind CSS 4** - Styling
- **Unity WebGL** - Character rendering and animation
- **Web Audio API** - Audio processing and analysis

## 🔐 Configuration

### Unity Build Settings
Ensure your Unity build exports these files:
- `model.loader.js`
- `model.framework.js`
- `model.wasm`
- `model.data`

### GameObject Names
Update these constants in your code if Unity uses different names:
```javascript
// In App.jsx
const goName = 'Epsilon';  // Change to match your GameObject

// In AudioSender.jsx
const audioGO = 'WebGLInputManagerGameObject';  // Change if needed
```

## 🧪 Testing

```bash
# Lint code
npm run lint

# Type check (if using TypeScript)
# npm run type-check
```

## 📝 Notes

- This is an **AI companion interface** - the character can be integrated with LLM APIs for conversational AI
- Unity `SendMessage` only accepts string parameters by default
- Complex data (arrays, objects) must be sent as JSON and parsed in Unity
- Audio context may be suspended until user interaction (browser policy)
- Large audio payloads can impact performance - consider chunking or compression
- The companion character (Epsilon) can display various emotional states through animation triggers

## 🚀 Future Enhancements

- [ ] Integrate with OpenAI/Anthropic APIs for conversational responses
- [ ] Add text-to-speech (TTS) for AI-generated audio
- [ ] Implement speech-to-text (STT) for voice input
- [ ] Add emotion detection from text sentiment
- [ ] WebSocket connection for real-time AI streaming responses
- [ ] Background environment picker
- [ ] Multiple character models
- [ ] Gesture and pose controls

## 💡 Use Cases

- **Virtual Assistants** - Customer support with a friendly face
- **Educational Companions** - Interactive tutors for e-learning
- **Healthcare** - Mental health support companions
- **Entertainment** - Interactive storytelling and gaming NPCs
- **Accessibility** - Visual interface for voice-based AI services

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request


**Need Help?** Check the browser console for Unity loader errors and `SendMessage` logs.

# iHub AI Character Assistant

This project is an interactive AI character assistant that combines a 3D character model with a conversational AI, featuring real-time voice interaction, 3D character animation synced with speech, and a web-based interface.

## About The Project

This application provides an immersive user experience with the following key features:

*   **Real-time Voice Interaction**: Speak to the AI character and get a voice response.
*   **3D Character Animation**: The 3D model is animated and lip-synced with the AI's speech.
*   **Speech-to-Text & Text-to-Speech**: Seamlessly converts your speech to text for the AI and the AI's text response back to speech.
*   **Web-Based Interface**: A modern and user-friendly interface built with React.
*   **Python Backend**: A powerful backend using FastAPI to handle AI processing and communication.

## Getting Started

To get a local copy up and running follow these simple steps.

### Prerequisites

Make sure you have the following installed on your system:

*   Node.js and npm (or yarn)
*   Python 3.7+ and pip

### Environment Variables

The backend uses environment variables for configuration. These are managed in a `.env` file in the `backend` directory.

1.  In the `backend` directory, create a copy of `.env.example` and name it `.env`.
2.  Open the `.env` file and add your configuration values.

Key variables include:
- `GOOGLE_API_KEY`: Your Google Gemini API key for LLM responses.
- `ALLOWED_ORIGINS`: A comma-separated list of allowed origins for CORS.

### Installation & Running

**1. Backend Setup**

First, set up and run the Python backend.

```bash
# Navigate to the backend directory
cd backend

# It is recommended to use a virtual environment
python -m venv venv
# On Windows, activate with:
# venv\Scripts\activate
# On macOS/Linux, activate with:
# source venv/bin/activate

# Install the required Python packages
pip install -r requirements.txt

# Run the script to load the model (if necessary)
python load_model.py

# Run the backend server
# The server will run on http://0.0.0.0:8000
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**2. Frontend Setup**

In a separate terminal, set up and run the React frontend.

```bash
# From the project root directory
# Install NPM packages
npm install

# Run the frontend development server
# The application will be available at http://localhost:5173 (or another port if 5173 is busy)
npm run dev
```

**3. Access the Application**

Once both the backend and frontend servers are running, open your web browser and navigate to the URL provided by the frontend development server (e.g., `http://localhost:5173`).

You should now be able to interact with the AI character assistant.

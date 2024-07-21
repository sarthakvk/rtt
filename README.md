
# Real-Time Translation Service (RTT) Prototype

## Overview

This prototype provides a real-time translation service that allows users speaking different languages to communicate seamlessly. Users can initiate a session via a web interface, specifying the language they will speak and the target language for translation. The system translates spoken input into text, converts it into the desired language, and then synthesizes speech output in the target language.

## Architecture

The project utilizes a modular architecture with the following key components:

- **Speech-to-Text (STT) and Translation Module (`sts.py`)**: Captures speech from users, transcribes it into text, and translates it using Azure Cognitive Services.
- **Text-to-Speech (TTS) Module (`tts.py`)**: Converts translated text into speech using Azure Cognitive Services.
- **Common Utilities (`common.py`)**: Provides shared resources such as language configurations and client setups.
- **Main Application (`main.py`)**: Manages WebSocket connections and coordinates the translation process. Contains the frontend as an HTML string for user interaction.

## System Design

### Components

1. **Backend**: 
   - Implemented with FastAPI to manage WebSocket connections.
   - Uses Azure Cognitive Services for STT, translation, and TTS functionality.
   - Supports OpenAI for text translation between languages but currently configured to use Azure.

2. **Frontend**:
   - Embedded within `main.py` as an HTML string.
   - JavaScript code to handle WebSocket communication.

### Data Flow

1. User selects source and target languages on the web interface.
2. User speech is captured and sent to the backend via WebSocket.
3. STT module transcribes the speech into text and translates it directly using Azure services.
4. Translated text is converted into speech using the TTS module.
5. Synthesized audio is sent back to the frontend and played to the user.

### Real-Time Streaming

The application achieves real-time translation and communication through the following mechanisms:

- **WebSocket Connections**: Maintains persistent connections between the client and server to allow continuous streaming of audio data. This ensures low latency communication.
- **Streaming Audio Processing**: Audio data is captured and sent to the server in small chunks, which are immediately processed by the STT and translation modules. This allows for quick feedback and minimizes delay.
- **Asynchronous Processing**: Uses asynchronous programming to handle multiple concurrent connections and process incoming audio streams without blocking the main execution thread. This helps in maintaining the responsiveness of the application even with multiple users.
- Although the tranlation only happens when we detect a complete sentence, this part is handled by azure's speech sdk

## Installation

To set up this project locally, follow these steps:

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd rtt
   ```

2. **Create and Activate a Virtual Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # On Windows, use `venv\Scripts\activate`
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirments.txt
   ```

4. **Set Up Environment Variables**:
   - Copy `.env.example` to `.env` and configure the required API keys for Azure and OpenAI.

## Usage

1. **Start the Application**:
   ```bash
   fastapi dev main.py
   ```

2. **Access the Frontend**:
   - Open a web browser and navigate to `http://localhost:8000`.

3. **Start a Translation Session**:
   - Select the source and target languages.
   - Speak into the microphone and listen to the translated output.

## Code Structure

- **`main.py`**: Configures the FastAPI server, handles WebSocket routes, and contains the frontend.
- **`tts.py`**: Implements text-to-speech conversion.
- **`sts.py`**: Implements speech-to-text transcription.
- **`common.py`**: Contains shared utilities and configurations.
- **`requirments.txt`**: Lists project dependencies.

>For questions or support, please contact me.

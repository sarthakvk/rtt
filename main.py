from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import asyncio

from .stt import get_speech_recognizer_audio_sink
from .common import Language

load_dotenv()
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
main_event_loop = asyncio.get_event_loop()

# Store WebSocket connections
connections = {}

html = """
<!DOCTYPE html>
<html>
<head>
    <title>WebSocket Audio Stream</title>
</head>
<body>
    <h1>WebSocket Audio Stream</h1>
    <label for="speak-language">Speak Language:</label>
    <select id="speak-language">
        <option value="en-US">English</option>
        <option value="es-ES">Spanish</option>
        <option value="hi-IN">Hindi</option>
    </select>
    <br>
    <label for="listen-language">Listen Language:</label>
    <select id="listen-language">
        <option value="en-US">English</option>
        <option value="es-ES">Spanish</option>
        <option value="hi-IN">Hindi</option>
    </select>
    <br>
    <button onclick="startStream()">Start Stream</button>
    <button onclick="stopStream()">Stop Stream</button>
    <script>
        var ws;
        var audioContext;
        var processor;
        var input;
        var globalStream;
        var audioBufferQueue = [];
        var source;
        var playing = false;

        function generateRandomString(length) {
            const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
            let result = '';
            const charactersLength = characters.length;
            for (let i = 0; i < length; i++) {
                result += characters.charAt(Math.floor(Math.random() * charactersLength));
            }
            return result;
        }

        function startStream() {
            const speakLanguage = document.getElementById('speak-language').value;
            const listenLanguage = document.getElementById('listen-language').value;
            rand_id = generateRandomString(10);
            ws = new WebSocket(`ws://localhost:8000/wss/${rand_id}/?speak=${speakLanguage}&listen=${listenLanguage}`);
            ws.binaryType = 'arraybuffer';  // Ensure binary data type
            ws.onopen = function(event) {
                console.log("WebSocket is open now.");
            };

            ws.onmessage = function(event) {
                if (typeof event.data === 'string') {
                    console.log("Message from server:", event.data);
                } else {
                    audioBufferQueue.push(event.data);
                    if (!playing) {
                        playAudio();
                        playing = true;
                    }
                }
            };

            ws.onclose = function(event) {
                console.log("WebSocket is closed now.");
            };

            navigator.mediaDevices.getUserMedia({ audio: true })
                .then(function(stream) {
                    globalStream = stream;
                    audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 24000 });
                    processor = audioContext.createScriptProcessor(4096, 1, 1);
                    input = audioContext.createMediaStreamSource(stream);
                    input.connect(processor);
                    processor.connect(audioContext.destination);
                    processor.onaudioprocess = function(e) {
                        if (ws.readyState === WebSocket.OPEN) {
                            var inputBuffer = e.inputBuffer.getChannelData(0);
                            var outputBuffer = new Int16Array(inputBuffer.length);
                            for (var i = 0; i < inputBuffer.length; i++) {
                                outputBuffer[i] = Math.max(-1, Math.min(1, inputBuffer[i])) * 0x7FFF;
                            }
                            ws.send(outputBuffer.buffer);
                        }
                    };
                })
                .catch(function(err) {
                    console.log("The following error occurred: " + err);
                });
        }

        function stopStream() {
            if (globalStream) {
                globalStream.getTracks().forEach(track => track.stop());
            }
            if (processor) {
                processor.disconnect();
            }
            if (input) {
                input.disconnect();
            }
            if (audioContext) {
                audioContext.close();
            }
            if (ws) {
                ws.close();
            }
            console.log("Stream stopped.");
        }

        function playAudio() {
            if (audioBufferQueue.length === 0) {
                // Create a silent buffer of 3200 samples if the queue is empty
                audioData = new ArrayBuffer(4000 * 2); // 4000 samples, 16-bit (2 bytes per sample)
            } else {
                audioData = audioBufferQueue.shift();
            }
            var audioBuffer = audioContext.createBuffer(1, audioData.byteLength / 2, 24000);
            var channelData = audioBuffer.getChannelData(0);

            var dataView = new DataView(audioData);
            for (var i = 0; i < channelData.length; i++) {
                channelData[i] = dataView.getInt16(i * 2, true) / 0x7FFF;
            }

            source = audioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(audioContext.destination);
            source.onended = playAudio;
            source.start();
        }
    </script>
</body>
</html>
"""


@app.get("/")
async def get():
    return HTMLResponse(html)


async def receive_audio(websocket: WebSocket, audio_stream, client_id: str):
    try:
        while True:
            data = await websocket.receive_bytes()
            audio_stream.write(data)
    except WebSocketDisconnect:
        pass


@app.websocket("/wss/{client_id}/")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: str,
    speak: str = Query(...),
    listen: str = Query(...),
):
    await websocket.accept()
    connections[client_id] = websocket

    # Convert query parameters to Language enum
    speak_language = Language(speak)
    listen_language = Language(listen)

    audio_stream, recognizer = get_speech_recognizer_audio_sink(
        client_id, connections, main_event_loop, speak_language, listen_language
    )

    try:
        await receive_audio(websocket, audio_stream, client_id)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        recognizer.stop_continuous_recognition_async()
        del connections[client_id]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

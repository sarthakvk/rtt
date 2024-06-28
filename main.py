from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
import asyncio

from .stt import get_speech_recognizer_audio_sink

load_dotenv()
app = FastAPI()
main_event_loop = asyncio.get_event_loop()

html = """
<!DOCTYPE html>
<html>
<head>
    <title>WebSocket Audio Stream</title>
</head>
<body>
    <h1>WebSocket Audio Stream</h1>
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

        function startStream() {
            ws = new WebSocket("ws://localhost:8000/ws");
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


async def receive_audio(websocket: WebSocket, audio_stream):
    try:
        while True:
            data = await websocket.receive_bytes()
            audio_stream.write(data)
    except WebSocketDisconnect:
        pass


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    audio_stream, recognizer = get_speech_recognizer_audio_sink(
        websocket, main_event_loop
    )

    try:
        await receive_audio(websocket, audio_stream)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        recognizer.stop_continuous_recognition_async()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

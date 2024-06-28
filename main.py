import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

from .stt import get_speech_recognizer_audio_sink

load_dotenv()
app = FastAPI()

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

            function startStream() {
                ws = new WebSocket("wss://0d4d-2405-201-6806-801b-d8c4-6dcc-29dc-c06.ngrok-free.app/ws");
                ws.binaryType = 'arraybuffer';  // Ensure binary data type
                ws.onopen = function(event) {
                    console.log("WebSocket is open now.");
                };

                ws.onmessage = function(event) {
                    console.log("Message from server:", event.data);
                };

                ws.onclose = function(event) {
                    console.log("WebSocket is closed now.");
                };

                navigator.mediaDevices.getUserMedia({ audio: true })
                    .then(function(stream) {
                        globalStream = stream;
                        audioContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
                        processor = audioContext.createScriptProcessor(4096, 1, 1);
                        input = audioContext.createMediaStreamSource(stream);
                        input.connect(processor);
                        processor.connect(audioContext.destination);
                        processor.onaudioprocess = function(e) {
                            var inputBuffer = e.inputBuffer.getChannelData(0);
                            var outputBuffer = new Int16Array(inputBuffer.length);
                            for (var i = 0; i < inputBuffer.length; i++) {
                                outputBuffer[i] = Math.max(-1, Math.min(1, inputBuffer[i])) * 0x7FFF;
                            }
                            ws.send(outputBuffer.buffer);
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
        </script>
    </body>
</html>
"""


@app.get("/")
async def get():
    return HTMLResponse(html)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    audio_stream, recognizer = get_speech_recognizer_audio_sink()
    try:
        while True:
            data = await websocket.receive_bytes()
            # print(len(data))
            audio_stream.write(data)

    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        recognizer.stop_continuous_recognition_async()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

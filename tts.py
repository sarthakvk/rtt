import os
from typing import Dict
import azure.cognitiveservices.speech as speechsdk
from .common import gpt_client, Language, AzureVoiceName
from azure.cognitiveservices.speech.audio import (
    PushAudioOutputStream,
    PushAudioOutputStreamCallback,
    AudioOutputConfig,
)
from asyncio import run_coroutine_threadsafe, get_event_loop
from fastapi import WebSocket


class WebsocketAudioOutputStream(PushAudioOutputStreamCallback):
    def __init__(self, client_id: str, websockets: Dict[str, WebSocket], event_loop):
        self.websockets = websockets
        self.event_loop = event_loop
        self.client_id = client_id
        self.env = os.getenv('ENV')

    def write(self, audio_buffer: memoryview) -> int:
        try:
            audio_data = audio_buffer.tobytes()

            if self.env == "DEV":
                websocket = self.websockets[self.client_id]
                future = run_coroutine_threadsafe(
                    websocket.send_bytes(audio_data), self.event_loop
                )
                future.result()
                return len(audio_data)

            for c_id, websocket in self.websockets.items():
                if not websocket and c_id == self.client_id:
                    continue
                future = run_coroutine_threadsafe(
                    websocket.send_bytes(audio_data), self.event_loop
                )
                future.result()

            return len(audio_data)
        except Exception as e:
            print(f"Error sending audio data: {e}")
        return 0

    def close(self):
        print("closed the output")


class TextToSpeech:
    def __init__(
        self,
        text_lang: Language,
        speech_lang: AzureVoiceName,
        output_callback: PushAudioOutputStreamCallback,
    ) -> None:
        self.text_lang = text_lang
        self.speech_lang = speech_lang
        self.speech_config = speechsdk.SpeechConfig(
            endpoint=f"wss://{os.getenv('AZURE_TTS_REGION')}.tts.speech.microsoft.com/cognitiveservices/websocket/v2",
            subscription=os.getenv("AZURE_TTS_API_KEY"),
        )
        self.speech_config.speech_recognition_language = speech_lang.value
        self.speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Raw24Khz16BitMonoPcm
        )
        properties = {
            "SpeechSynthesis_FrameTimeoutInterval": "100000000",
            "SpeechSynthesis_RtfTimeoutThreshold": "10",
        }
        self.speech_config.set_properties_by_name(properties)
        self.out_stream = PushAudioOutputStream(output_callback)
        audio_config = AudioOutputConfig(stream=self.out_stream)

        self.speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config, audio_config=audio_config
        )

    def set_speech_synthesizing_callback(self, callback):
        self.speech_synthesizer.synthesizing.connect(callback)

    def set_speech_synthesized_callback(self, callback):
        self.speech_synthesizer.synthesis_completed.connect(callback)

    def write_translated(self, text: str):
        self.tts_request.input_stream.write(text)
        print("translation written to output buffer")

    def translate_generator(self, text: str):
        completion = gpt_client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a true translator, "
                        "Input will be a speech to text output"
                        f", correct the input if necessary and translate it to {self.speech_lang.name}"
                        ", incase no text is provided, don't output anything"
                    ),
                },
                {"role": "user", "content": f"{text}"},
            ],
            stream=True,
        )

        for chunk in completion:
            if len(chunk.choices) > 0:
                chunk_text = chunk.choices[0].delta.content
                if chunk_text:
                    yield chunk_text

    def close(self):
        # print("closing input stream")
        self.tts_request.input_stream.close()
        # print("Closed inp stream")

    def open(self):
        self.tts_request = speechsdk.SpeechSynthesisRequest(
            input_type=speechsdk.SpeechSynthesisRequestInputType.TextStream
        )

        return self.speech_synthesizer.speak_async(self.tts_request)

    def __enter__(self):
        self.open()
        return self

    def __exit__(self):
        self.close()
        return False

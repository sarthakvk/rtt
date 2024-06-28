import os
from openai import OpenAI
import azure.cognitiveservices.speech as speechsdk
from .common import gpt_client, Language, AzureVoiceName


class TextToSpeech:
    def __init__(self, text_lang: Language, speech_lang: AzureVoiceName) -> None:
        self.text_lang = text_lang
        self.speech_lang = speech_lang
        self.speech_config = speechsdk.SpeechConfig(
            subscription=os.getenv("AZURE_TTS_API_KEY"),
            region=os.getenv("AZURE_TTS_REGION"),
            speech_recognition_language=speech_lang,
        )
        properties = {
            "SpeechSynthesis_FrameTimeoutInterval": "100000000",
            "SpeechSynthesis_RtfTimeoutThreshold": "10",
        }
        self.speech_config.set_properties_by_name(properties)

        self.speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=self.speech_config
        )

        self.tts_request = speechsdk.SpeechSynthesisRequest(
            input_type=speechsdk.SpeechSynthesisRequestInputType.TextStream
        )

    def set_speech_synthesizing_callback(self, callback):
        self.speech_synthesizer.synthesizing.connect(callback)

    def set_speech_synthesized_callback(self, callback):
        self.speech_synthesizer.synthesis_completed.connect(callback)

    def write_translated(self, text: str):
        out = ""
        for translated_text in self.translate_generator(text):
            out += translated_text
            self.tts_request.input_stream.write(translated_text)
        self.speech_synthesizer.speak_text_async(out)
    def translate_generator(self, text: str):
        completion = gpt_client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a true translator, "
                        "Input will be a speech to text"
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
        self.tts_request.input_stream.close()

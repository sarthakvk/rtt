"""Speech to text"""

import os
from typing import Tuple
import azure.cognitiveservices.speech as speechsdk
from .tts import TextToSpeech
from .common import Language, AzureVoiceName

speech_config = speechsdk.SpeechConfig(
    subscription=os.getenv("AZURE_TTS_API_KEY"), region=os.getenv("AZURE_TTS_REGION")
)
speech_config.speech_recognition_language = "en-US"

tts = TextToSpeech(text_lang=Language.ENGLISH, speech_lang=AzureVoiceName.SPANISH)


def recognized_callback(evt):
    print(evt.result.text)
    tts.write_translated(evt.result.text)


def get_speech_recognizer_audio_sink() -> (
    Tuple[speechsdk.audio.PushAudioInputStream, speechsdk.SpeechRecognizer]
):
    audio_stream = speechsdk.audio.PushAudioInputStream(
        speechsdk.audio.AudioStreamFormat(samples_per_second=16000)
    )
    audio_config = speechsdk.audio.AudioConfig(stream=audio_stream)

    speech_recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config, audio_config=audio_config
    )
    speech_recognizer.recognized.connect(recognized_callback)
    # speech_recognizer.recognizing.connect(recognizing_callback)
    speech_recognizer.session_started.connect(lambda e: print("session started"))
    speech_recognizer.session_stopped.connect(lambda e: print("session stopped"))
    speech_recognizer.canceled.connect(lambda e: print("session cancelled"))

    speech_recognizer.start_continuous_recognition_async()

    return audio_stream, speech_recognizer

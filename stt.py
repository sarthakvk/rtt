"""Speech to text"""

from functools import partial
import os
from typing import Tuple
import azure.cognitiveservices.speech as speechsdk
from .tts import TextToSpeech, WebsocketAudioOutputStream
from .common import Language, AzureVoiceName

speech_config = speechsdk.SpeechConfig(
    subscription=os.getenv("AZURE_TTS_API_KEY"), region=os.getenv("AZURE_TTS_REGION")
)
speech_config.speech_recognition_language = Language.ENGLISH.value


def recognized_callback(
    client_id, connections, event_loop, evt: speechsdk.SpeechRecognitionEventArgs
):
    tts = TextToSpeech(
        Language.ENGLISH,
        AzureVoiceName.SPANISH,
        WebsocketAudioOutputStream(client_id, connections, event_loop),
    )
    try:
        print(evt.result.text)
        if evt.result.text:
            tsk = tts.open()
            tts.write_translated(evt.result.text)
            tts.close()
            res = tsk.get()
            print(res)
    except Exception as e:
        print(e)


def get_speech_recognizer_audio_sink(
    client_id, connections, event_loop
) -> Tuple[speechsdk.audio.PushAudioInputStream, speechsdk.SpeechRecognizer]:
    audio_stream = speechsdk.audio.PushAudioInputStream(
        speechsdk.audio.AudioStreamFormat(samples_per_second=16000)
    )
    audio_config = speechsdk.audio.AudioConfig(stream=audio_stream)

    speech_recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config,
        audio_config=audio_config,
        language=Language.HINDI.value,
    )

    partial_recognized_callback = partial(
        recognized_callback, client_id, connections, event_loop
    )
    speech_recognizer.recognized.connect(partial_recognized_callback)
    # speech_recognizer.recognizing.connect(recognizing_callback)
    speech_recognizer.session_started.connect(lambda e: print("session started"))
    speech_recognizer.session_stopped.connect(lambda e: print("session stopped"))
    speech_recognizer.canceled.connect(lambda e: print("session cancelled"))

    speech_recognizer.start_continuous_recognition_async()

    return audio_stream, speech_recognizer

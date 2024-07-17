"""Speech to text"""

from functools import partial
import os
from typing import Tuple
import azure.cognitiveservices.speech as speechsdk
from .tts import TextToSpeech, WebsocketAudioOutputStream
from .common import Language, AzureVoiceName


def recognized_callback(
    tts: TextToSpeech, evt: speechsdk.SpeechRecognitionEventArgs
):
    try:
        if evt.result.reason == speechsdk.ResultReason.TranslatedSpeech and evt.result.translations:
            text = next(iter(evt.result.translations.values()))
            print(text)
            tsk = tts.open()
            tts.write_translated(text)
            tts.close()
            res = tsk.get()
    except Exception as e:
        print(e)


def get_speech_recognizer_audio_sink(
    client_id, connections, event_loop, speak_lang: Language, listen_lang: Language
) -> Tuple[speechsdk.audio.PushAudioInputStream, speechsdk.SpeechRecognizer]:
    translation_config = speechsdk.translation.SpeechTranslationConfig(
        subscription=os.getenv("AZURE_TTS_API_KEY"), region=os.getenv("AZURE_TTS_REGION")
    )
    translation_config.speech_recognition_language = speak_lang.value
    translation_config.add_target_language(listen_lang.value)
    audio_stream = speechsdk.audio.PushAudioInputStream(
        speechsdk.audio.AudioStreamFormat(samples_per_second=16000)
    )
    audio_config = speechsdk.audio.AudioConfig(stream=audio_stream)

    speech_recognizer = speechsdk.translation.TranslationRecognizer(
        translation_config=translation_config,
        audio_config=audio_config,
    )

    tts = TextToSpeech(
        speak_lang,
        listen_lang,
        WebsocketAudioOutputStream(client_id, connections, event_loop),
    )

    partial_recognized_callback = partial(
        recognized_callback, tts
    )
    speech_recognizer.recognized.connect(partial_recognized_callback)
    # speech_recognizer.recognizing.connect(recognizing_callback)
    speech_recognizer.session_started.connect(lambda e: print("session started"))
    speech_recognizer.session_stopped.connect(lambda e: print("session stopped"))
    speech_recognizer.canceled.connect(lambda e: print("session cancelled"))

    speech_recognizer.start_continuous_recognition_async()

    return audio_stream, speech_recognizer

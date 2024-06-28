import os
import time
from openai import OpenAI
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

load_dotenv()

# setup AzureOpenAI client
gpt_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# setup speech synthesizer
# IMPORTANT: MUST use the websocket v2 endpoint
speech_config = speechsdk.SpeechConfig(
    endpoint=f"wss://{os.getenv('AZURE_TTS_REGION')}.tts.speech.microsoft.com/cognitiveservices/websocket/v2",
    subscription=os.getenv("AZURE_TTS_API_KEY"),
)

speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)

speech_synthesizer.synthesizing.connect(lambda evt: print("[audio]", end=""))

# set a voice name
speech_config.speech_synthesis_voice_name = "en-US-AvaMultilingualNeural"

# set timeout value to bigger ones to avoid sdk cancel the request when GPT latency too high
properties = dict()
properties["SpeechSynthesis_FrameTimeoutInterval"] = "100000000"
properties["SpeechSynthesis_RtfTimeoutThreshold"] = "10"
speech_config.set_properties_by_name(properties)

# create request with TextStream input type
tts_request = speechsdk.SpeechSynthesisRequest(
    input_type=speechsdk.SpeechSynthesisRequestInputType.TextStream
)
tts_task = speech_synthesizer.speak_async(tts_request)

# Get GPT output stream
# completion = gpt_client.chat.completions.create(
#     model="gpt-3.5-turbo",
#     messages=[
#         {"role": "system", "content": "You are a helpful assistant."},
#         {"role": "user", "content": "tell me a joke in 10 words"},
#     ],
#     stream=True,
# )

for chunk in ["My ", "name ", "is ", "sarthak"]:
    print(chunk, end="")
    tts_request.input_stream.write(chunk)
    # time.sleep(1)
print("[GPT END]", end="")

# close tts input stream when GPT finished
tts_request.input_stream.close()

# wait all tts audio bytes return
result = tts_task.get()
print("[TTS END]", end="")

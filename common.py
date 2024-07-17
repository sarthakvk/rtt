import os
from openai import OpenAI
import enum
from dotenv import load_dotenv

load_dotenv()

gpt_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


class AzureVoiceName(str, enum.Enum):
    SPANISH = "es-ES-ElviraNeural"
    ENGLISH = "en-IN-Ravi"
    HINDI = "hi-IN-SwaraNeural"


class Language(str, enum.Enum):
    ENGLISH = "en-US"
    SPANISH = "es-ES"
    HINDI = "hi-IN"

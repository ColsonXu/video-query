import os
import assemblyai as aai
from dotenv import load_dotenv

load_dotenv()

aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")
transcriber = aai.Transcriber()

def transcribe(file):
    return transcriber.transcribe(file).text

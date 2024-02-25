import os
import assemblyai as aai

aai.settings.api_key = os.environ["ASSEMBLYAI_API_KEY"]
transcriber = aai.Transcriber()

def transcribe(file):
    return transcriber.transcribe(file).text

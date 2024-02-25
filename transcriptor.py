import assemblyai as aai
from env import ASSEMBLYAI

aai.settings.api_key = ASSEMBLYAI
transcriber = aai.Transcriber()

def transcribe(file):
    return transcriber.transcribe(file).text

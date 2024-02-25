from youtube_transcript_api import YouTubeTranscriptApi
import re

def _get_video_id(youtube_url):
    # Regular expression for extracting the video ID from various YouTube URL formats
    regex = r'(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
    matches = re.search(regex, youtube_url)
    if matches:
        return matches.group(1)
    else:
        return None

def get_caption_from_youtube(url):
    id = _get_video_id(url)
    srt = YouTubeTranscriptApi.get_transcript(id)

    text = " ".join([dict['text'] for dict in srt])
    paren_removed = re.sub(r'\(.*?\)', '', text)
    pure_transcript = re.sub(r'\n', ' ', paren_removed)

    return pure_transcript
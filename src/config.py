# Configuration and environment setup
from dotenv import load_dotenv
import os
from groq import Groq

# Load environment variables
load_dotenv()

# Initialize Groq client
GROQ_CLIENT = Groq(api_key=os.environ["GROQ_API_KEY"])

# Audio file paths
AUDIO_PATHS = {
    'play': "audio/play.mp3",
    'spin': "audio/spin.mp3",
    'submit': "audio/submit.mp3",
    'option': "audio/option.mp3",
    'end_game': "audio/end-game.mp3"
}
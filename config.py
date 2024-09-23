# config.py

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    API_ENDPOINT = "https://api.openai.com/v1/chat/completions"  # Replace with actual endpoint
    SUPPORTED_LANGUAGES = ["Python", "JavaScript", "Java"]
    CACHE_MAXSIZE = 128  # Maximum number of cached prompts
    CACHE_TTL = 300  # Time-to-live for cache in seconds
    LOG_FILE = "codeassist.log"

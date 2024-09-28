# backend/config.py

import os
from dotenv import load_dotenv

load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# YouTube API configuration
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# OpenAI API configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# AssemblyAI API configuration (if still needed)
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")

# CORS configuration
ORIGINS = [
    "*",  # In production, specify the exact origin
]

# Default configuration values
NUM_TAGS_DEFAULT = 5
MAX_CONCURRENT_REQUESTS = 10
SENTENCE_TRANSFORMER_MODEL = 'paraphrase-MiniLM-L6-v2'

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
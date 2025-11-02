"""
Configuration for stream monitoring
"""
import os

# Stream Configuration
STREAM_URL = "https://dcs-live-uc1.mp.lura.live/server/play/5Awwm3GfagVzfpdA/rendition.m3u8?track=video-0&anvsid=m177626883-n086fddb1148a7dcbf6ecea728fb62c47&ts=1762096632&anvtrid=f7a3691c3866713305634146cb0edcc8"
CHUNK_DURATION = 60  # seconds - 1 minute chunks
AUDIO_FORMAT = "wav"
SAMPLE_RATE = 16000  # Required for Whisper

# Directory paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
AUDIO_CHUNKS_DIR = os.path.join(DATA_DIR, "audio_chunks")
OUTPUTS_DIR = os.path.join(DATA_DIR, "outputs")

# Create directories if they don't exist
os.makedirs(AUDIO_CHUNKS_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)

# Whisper X Configuration (FREE)
WHISPER_MODEL = "base"  # Options: tiny, base, small, medium, large-v2
DEVICE = "cpu"  # Use "cuda" if you have GPU
COMPUTE_TYPE = "int8"  # For CPU efficiency

# LLM Configuration (FREE using Hugging Face)
SUMMARIZATION_MODEL = "facebook/bart-large-cnn"  # Free summarization model
MAX_SUMMARY_LENGTH = 15  # words

# API Configuration
FLASK_PORT = 5000
FLASK_HOST = "0.0.0.0"

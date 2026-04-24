"""
Configuration for the Bounded Emotion Memory System.
All time values are in minutes.
"""
import os

# Base directory of this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# RAG knowledge base directory
RAG_DOCS_DIR = os.path.join(BASE_DIR, "rag_docs_v2")

# Emotion detection interval (minutes)
# Set to 1 to match the app's RunPod inference interval (every 60 seconds)
EMOTION_CHECK_INTERVAL = 1  # How often emotion is detected

# Temporal relevance threshold (minutes)
# Scaled down from 10 to 3 to match the 1-min check interval
T_RECENT = 3   # Previous emotion is relevant only if changed within this window

# Periodic feedback interval (minutes)
# Generate feedback every 5 minutes when emotion persists (scaled from 10 min)
FEEDBACK_INTERVAL = 5   # Generate feedback every 5 minutes when emotion persists

# LLM Configuration
LLM_MODEL = "phi3"  # Using local Phi-3 model via Ollama
LLM_TEMPERATURE = 0.7
LLM_MAX_OUTPUT_TOKENS = 150
OLLAMA_BASE_URL = "http://localhost:11434"

# Weather API Configuration
WEATHER_API_KEY = None  # Set via environment variable OPENWEATHER_API_KEY
WEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather"

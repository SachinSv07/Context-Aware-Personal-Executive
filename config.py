"""
Configuration file for Context-Aware Personal Executive
Shared across all modules - no merge conflicts expected
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent
SAMPLE_DATA_DIR = PROJECT_ROOT / "sample_data"
TOOLS_DIR = PROJECT_ROOT / "tools"
AGENT_DIR = PROJECT_ROOT / "agent"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

# Gemini Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your-gemini-api-key-here")
GEMINI_MODEL = "gemini-2.0-flash"  # or "gemini-1.5-pro" for higher quality

# Data source paths
EMAIL_DATA_PATH = SAMPLE_DATA_DIR / "emails.json"
PDF_DATA_PATH = SAMPLE_DATA_DIR / "documents.pdf"
CSV_DATA_PATH = SAMPLE_DATA_DIR / "notes.csv"
GMAIL_TOKEN_PATH = SAMPLE_DATA_DIR / "gmail_token.json"

# Search settings
MAX_SEARCH_RESULTS = 5
SIMILARITY_THRESHOLD = 0.7

# Agent settings
AGENT_TEMPERATURE = 0.7
MAX_AGENT_ITERATIONS = 3

# Frontend settings
STREAMLIT_PORT = 8501
FLASK_PORT = 5000
FLASK_DEBUG = True

# Logging
LOG_LEVEL = "INFO"

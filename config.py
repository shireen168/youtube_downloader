"""Configuration settings for the YouTube Downloader."""

import os
from pathlib import Path

# Constants
VIDEO_FORMATS = [("MP4 files", "*.mp4"), ("MP3 files", "*.mp3")]
DEFAULT_DOWNLOAD_DIR = str(Path.home() / "Downloads")

# Format configurations
FORMAT_CONFIGS = {
    "mp4": {
        "format": "best",
        "postprocessors": [],
        "extract_flat": "in_playlist",
        "ignoreerrors": True,
        "nooverwrites": True,
        "playlist": True
    },
    "mp3": {
        "format": "best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
        "extract_flat": "in_playlist",
        "ignoreerrors": True,
        "nooverwrites": True,
        "playlist": True
    },
}

# Custom CSS
CUSTOM_CSS = """
<style>
    /* Button styling */
    .stButton > button, .stDownloadButton > button {
        width: auto !important;
        min-width: 120px !important;
        background-color: #FF0000 !important;
        color: white !important;
        border: none !important;
        padding: 8px 24px !important;
        border-radius: 4px !important;
        font-weight: bold !important;
        font-size: 1rem !important;
        min-height: 40px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        box-shadow: none !important;
        margin: 0 auto !important;
    }
    
    .stButton > button:hover, .stDownloadButton > button:hover {
        background-color: #CC0000 !important;
    }

    /* Center align buttons */
    div[data-testid="column"] > div[data-testid="stVerticalBlock"] > div > div > div {
        display: flex !important;
        justify-content: center !important;
    }

    /* Success and error messages */
    .success-message {
        padding: 1rem;
        border-radius: 5px;
        background-color: #043927;
        color: #ffffff;
        margin: 0.5rem 0;
    }
    
    .error-message {
        padding: 1rem;
        border-radius: 5px;
        background-color: #3d0c11;
        color: #ffffff;
        margin: 0.5rem 0;
    }
    
    /* Footer styling */
    .footer {
        text-align: center;
        padding: 1rem;
        color: #666;
        position: fixed;
        bottom: 0;
        left: 0;
        width: 100%;
        background-color: #0E1117;
        border-top: 1px solid #333;
    }
</style>
"""

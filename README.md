# YouTube Downloader

A simple Python script to download YouTube videos using yt-dlp.

## Prerequisites

- Python 3.x installed on your system

## Setup Instructions

1. Clone this repository:
```bash
git clone https://github.com/shireen168/youtube_downloader.git
cd youtube_downloader
```

2. Create a virtual environment:
```bash
python -m venv .venv
```

3. Activate the virtual environment:
   - On Windows:
   ```bash
   .venv\Scripts\activate
   ```
   - On macOS/Linux:
   ```bash
   source .venv/bin/activate
   ```

4. Install required packages:
```bash
pip install yt-dlp
```

## Usage

1. Make sure your virtual environment is activated (see step 3 above)

2. Run the script:
```bash
python youtube_downloader.py
```

3. When prompted, enter the YouTube URL of the video you want to download

4. The video will be downloaded to the current directory

## Features

- Downloads YouTube videos in the highest available quality
- Simple command-line interface
- Progress bar showing download status
- Error handling for invalid URLs

## Deactivating the Virtual Environment

When you're done using the downloader, you can deactivate the virtual environment by simply typing:
```bash
deactivate
```

## Note

The virtual environment (.venv folder) is specific to this project and can be safely deleted and recreated if needed. Just follow the setup instructions again to recreate it.

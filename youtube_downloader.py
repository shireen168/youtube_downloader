"""Enhanced YouTube Playlist Downloader using yt-dlp"""

import yt_dlp
from pathlib import Path
import time

def progress_hook(d):
    if d['status'] == 'downloading':
        print(f"Downloading: {d.get('filename', 'Unknown')} - {d.get('_percent_str', '0.0%')}")
    elif d['status'] == 'finished':
        print("Download finished, now post-processing...")

def download_video(url, output_path='downloads'):
    output_dir = Path(output_path)
    output_dir.mkdir(parents=True, exist_ok=True)

    ydl_opts = {
        'format': 'best',
        'outtmpl': str(output_dir / '%(title)s.%(ext)s'),
        'quiet': False,  # Enable detailed logging
        'progress_hooks': [progress_hook],
        'socket_timeout': 30,
        'retries': 5,
        'ignoreerrors': True,  # Continue on download errors
        # 'logger': yt_dlp.logger.Logger(),  # Removed to fix AttributeError
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            print("Starting download...")
            ydl.download([url])
            print("Download completed!")
            time.sleep(2)  # Delay between downloads
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == "__main__":
    url = input("Enter YouTube URL: ").strip()
    if not url:
        print("Please enter a URL.")
    else:
        download_video(url)
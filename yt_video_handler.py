"""YouTube video and playlist downloader implementation."""

import os
import tempfile
import zipfile
from typing import Tuple, Optional, Callable

import yt_dlp
import streamlit as st

from config import FORMAT_CONFIGS


class YouTubeDownloader:
    """Handles downloading of YouTube videos and playlists."""

    def __init__(self, progress_callback: Optional[Callable] = None):
        """Initialize the downloader with optional progress callback."""
        self.progress_callback = progress_callback
        self.downloading = False
        self.current_video = ""
        self.total_videos = 0
        # Ensure temp directory exists
        self.temp_dir = tempfile.mkdtemp()
        os.makedirs(self.temp_dir, exist_ok=True)

    def __del__(self):
        """Cleanup temporary files."""
        try:
            if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
                for root, dirs, files in os.walk(self.temp_dir, topdown=False):
                    for name in files:
                        try:
                            os.remove(os.path.join(root, name))
                        except:
                            pass
                    for name in dirs:
                        try:
                            os.rmdir(os.path.join(root, name))
                        except:
                            pass
                try:
                    os.rmdir(self.temp_dir)
                except:
                    pass
        except:
            pass

    @staticmethod
    def is_playlist_url(url: str) -> bool:
        """Check if the URL is a YouTube playlist."""
        return "playlist" in url or "&list=" in url

    def create_progress_hook(self, progress_bar, status_text) -> Tuple[Callable, Callable]:
        """Create a progress hook for tracking download progress."""
        temp_file_path = None
        video_title = None
        download_complete = False
        download_data = None

        def progress_hook(d):
            nonlocal temp_file_path, video_title, download_complete, download_data

            if not self.downloading:
                raise Exception("Download cancelled by user")

            if d["status"] == "downloading":
                try:
                    # Update current video info for playlists
                    if "info_dict" in d:
                        info = d["info_dict"]
                        if "playlist_count" in info:
                            self.total_videos = info["playlist_count"]
                        if "playlist_index" in info:
                            current_index = info["playlist_index"]
                            self.current_video = f"Video {current_index} of {self.total_videos}"

                    downloaded = d.get("downloaded_bytes", 0)
                    total = d.get("total_bytes", 0) or d.get("total_bytes_estimate", 0)

                    if total > 0:
                        percent = min(100.0, (downloaded / total) * 100)
                        progress_bar.progress(percent / 100)

                        # Format downloaded size
                        downloaded_mb = downloaded / (1024 * 1024)
                        total_mb = total / (1024 * 1024)
                        
                        # Create a more visible progress display
                        progress_info = f"""
                        {self.current_video}
                        ⏳ Progress: {percent:.1f}%
                        📥 Downloaded: {downloaded_mb:.1f}MB / {total_mb:.1f}MB
                        """
                        status_text.text(progress_info)

                except (ValueError, AttributeError, ZeroDivisionError) as e:
                    if self.progress_callback:
                        self.progress_callback(f"Error calculating progress: {str(e)}")
                    pass

                temp_file_path = d.get("filename")
                video_title = d.get("info_dict", {}).get("title", "video")

            elif d["status"] == "finished":
                status = "✅ Processing video..."
                if self.total_videos > 1:
                    status = f"{self.current_video}\n{status}"
                status_text.text(status)
                progress_bar.progress(1.0)
                download_complete = True

                # Read the file data for download
                if temp_file_path and os.path.exists(temp_file_path):
                    with open(temp_file_path, "rb") as f:
                        download_data = f.read()

        return progress_hook, lambda: (video_title, download_complete, download_data)

    def handle_download_error(self, error_msg: str) -> Optional[str]:
        """Convert technical error messages to user-friendly ones."""
        error_mappings = {
            "ERROR: No video formats found": "Could not find any video formats. Please check if the URL is correct.",
            "HTTP Error 404": "Video not found. Please check if the URL is correct.",
            "HTTP Error 403": "Access denied. This video might be private or region-restricted.",
            "Incomplete data received": "Download failed due to network issues. Please try again.",
            "Unable to download webpage": "Could not access YouTube. Please check your internet connection.",
            "Video unavailable": "This video is unavailable. It might have been removed or made private.",
            "Sign in to confirm your age": "Age-restricted video. Unable to download.",
            "main thread": None  # Special case: handle silently
        }

        for error_key, friendly_message in error_mappings.items():
            if error_key in error_msg:
                return friendly_message

        return f"Error: {error_msg}"

    def download(self, url: str, format_type: str, progress_bar, status_text) -> Tuple[bool, str, str, Optional[bytes]]:
        """
        Download a YouTube video or playlist.

        Args:
            url: YouTube video or playlist URL
            format_type: Format to download (mp4 or mp3)
            progress_bar: Streamlit progress bar
            status_text: Streamlit text element for status

        Returns:
            Tuple containing (success, message, title, download_data)
        """
        try:
            self.downloading = True
            is_playlist = self.is_playlist_url(url)

            progress_hook, get_download_info = self.create_progress_hook(
                progress_bar, status_text
            )

            format_config = FORMAT_CONFIGS[format_type]
            
            # Configure yt-dlp options with better error handling
            ydl_opts = {
                "format": format_config["format"],
                "outtmpl": os.path.join(self.temp_dir, "%(title)s.%(ext)s"),
                "progress_hooks": [progress_hook],
                "postprocessors": format_config["postprocessors"],
                "extract_flat": format_config.get("extract_flat"),
                "ignoreerrors": True,  # Don't stop on download errors
                "nooverwrites": True,  # Don't overwrite files
                "quiet": True,
                "no_warnings": True,
                "nocheckcertificate": True,  # Skip HTTPS certificate validation
                "socket_timeout": 30,  # Increase timeout
                "retries": 10,  # Number of retries for http/download
                "fragment_retries": 10,  # Number of retries for ts fragments
                "hls_prefer_native": True,  # Use native HLS downloader
            }

            if is_playlist:
                # For playlists, we want to download all videos
                ydl_opts.update({
                    "extract_flat": False,  # We want full extraction for playlists
                    "yes_playlist": True,
                    "playlist_items": "1-50"  # Limit to first 50 videos for safety
                })
            else:
                # For single videos, disable playlist features
                ydl_opts.update({
                    "noplaylist": True
                })

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # Extract info first to get video/playlist details
                    info = ydl.extract_info(url, download=False)
                    
                    if is_playlist:
                        playlist_title = info.get('title', 'Playlist')
                        self.total_videos = len(info.get('entries', []))
                        
                        # Create a zip file for the playlist
                        zip_path = os.path.join(self.temp_dir, f"{playlist_title}.zip")
                        
                        # Download the videos
                        ydl.download([url])
                        
                        # Create zip file of downloaded content
                        with zipfile.ZipFile(zip_path, 'w') as zipf:
                            for file in os.listdir(self.temp_dir):
                                if file != os.path.basename(zip_path):  # Don't include the zip file itself
                                    file_path = os.path.join(self.temp_dir, file)
                                    zipf.write(file_path, os.path.basename(file_path))
                        
                        # Read the zip file
                        with open(zip_path, 'rb') as f:
                            download_data = f.read()
                        
                        return True, "✅ Playlist downloaded successfully!", playlist_title, download_data
                    else:
                        # Single video download
                        ydl.download([url])
                        video_title, download_complete, download_data = get_download_info()
                        
                        if download_complete and download_data:
                            return True, "✅ Video downloaded successfully!", video_title, download_data
                        else:
                            return False, "❌ Download incomplete or file not found.", None, None

            except Exception as e:
                error_msg = self.handle_download_error(str(e))
                if error_msg:
                    return False, f"❌ {error_msg}", None, None
                raise  # Re-raise if no specific error message

        except Exception as e:
            error_msg = str(e)
            if "Download cancelled by user" in error_msg:
                return False, "❌ Download cancelled by user.", None, None
            return False, f"❌ An error occurred: {error_msg}", None, None

        finally:
            self.downloading = False
            # Cleanup temp files
            try:
                for file in os.listdir(self.temp_dir):
                    try:
                        os.remove(os.path.join(self.temp_dir, file))
                    except:
                        pass
            except:
                pass

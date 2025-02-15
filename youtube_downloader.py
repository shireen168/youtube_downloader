import os
import tempfile
import time
from pathlib import Path
import streamlit as st
import yt_dlp

# Constants
VIDEO_FORMATS = [("MP4 files", "*.mp4")]
DEFAULT_DOWNLOAD_DIR = str(Path.home() / "Downloads")

# Custom CSS
CUSTOM_CSS = """
<style>
    .stop-button {
        background-color: #ff4b4b !important;
        color: white !important;
        border-color: #ff4b4b !important;
    }
    </style>
"""

def init_session_state():
    """Initialize Streamlit session state variables."""
    if "downloading" not in st.session_state:
        st.session_state.downloading = False
    if "download_data" not in st.session_state:
        st.session_state.download_data = None


def setup_page():
    """Configure the Streamlit page settings."""
    st.set_page_config(
        page_title="YouTube Video Downloader",
        page_icon="🎥",
        layout="centered"
    )
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def create_progress_hook(progress_bar, status_text):
    """Create a progress hook for tracking download progress."""
    temp_file_path = None
    video_title = None
    download_complete = False
    download_data = None

    def progress_hook(d):
        nonlocal temp_file_path, video_title, download_complete, download_data

        if not st.session_state.downloading:
            raise Exception("Download cancelled by user")

        if d["status"] == "downloading":
            try:
                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes', 0) or d.get('total_bytes_estimate', 0)
                
                if total > 0:
                    percent = min(100.0, (downloaded / total) * 100)
                    progress_bar.progress(percent / 100)
                    
                    # Format downloaded size
                    downloaded_mb = downloaded / (1024 * 1024)
                    total_mb = total / (1024 * 1024)
                    status = f"⏳ Downloading: {percent:.1f}% ({downloaded_mb:.1f}MB of {total_mb:.1f}MB)"
                    status_text.text(status)
                
            except (ValueError, AttributeError, ZeroDivisionError) as e:
                st.error(f"Error calculating progress: {str(e)}")
                pass

            temp_file_path = d.get("filename")
            video_title = d.get("info_dict", {}).get("title", "video")

        elif d["status"] == "finished":
            status_text.text("✅ Download completed! Processing video...")
            progress_bar.progress(1.0)
            download_complete = True
            
            # Read the file data for download
            if temp_file_path and os.path.exists(temp_file_path):
                with open(temp_file_path, 'rb') as f:
                    download_data = f.read()
                st.session_state.download_data = download_data

    return progress_hook, lambda: (video_title, download_complete, download_data)


def handle_download_error(error_msg):
    """Convert technical error messages to user-friendly ones."""
    if "ERROR: No video formats found" in error_msg:
        return "Could not find any video formats. Please check if the URL is correct."
    if "HTTP Error 404" in error_msg:
        return "Video not found. Please check if the URL is correct."
    if "HTTP Error 403" in error_msg:
        return "Access denied. This video might be private or region-restricted."
    if "Incomplete data received" in error_msg:
        return "Download failed due to network issues. Please try again."
    if "Unable to download webpage" in error_msg:
        return "Could not access YouTube. Please check your internet connection."
    if "Video unavailable" in error_msg:
        return "This video is unavailable. It might have been removed or made private."
    if "Sign in to confirm your age" in error_msg:
        return "Age-restricted video. Unable to download."
    if "main thread" in error_msg:
        return None  # Special case: handle silently
    return f"Error: {error_msg}"


def download_video(url, stop_button_container):
    """
    Download a YouTube video and track its progress.

    Args:
        url (str): YouTube video URL
        stop_button_container: Streamlit container for the stop button

    Returns:
        tuple: (success, message, video_title, download_data)
    """
    try:
        st.session_state.downloading = True
        st.session_state.download_data = None

        with tempfile.TemporaryDirectory() as temp_dir:
            progress_bar = st.progress(0)
            status_text = st.empty()

            progress_hook, get_status = create_progress_hook(progress_bar, status_text)

            # Ensure temp_dir is a Path object for proper Unicode handling
            temp_dir_path = Path(temp_dir)
            ydl_opts = {
                "format": "best",
                "outtmpl": str(temp_dir_path / "%(title)s.%(ext)s"),
                "progress_hooks": [progress_hook],
            }

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    video_title = info.get("title", "video")
                    # Sanitize the video title to remove problematic characters
                    video_title = "".join(c for c in video_title if c not in r'<>:"/\|?*')
                    status_text.text(f"Starting download of: {video_title}")
                    ydl.download([url])
            except Exception as e:
                if str(e) == "Download cancelled by user":
                    status_text.text("❌ Download cancelled")
                    progress_bar.empty()
                    return False, "Download cancelled by user.", None, None
                raise e
            finally:
                st.session_state.downloading = False

            video_title, download_complete, download_data = get_status()

            if download_complete and download_data:
                return True, "Video downloaded successfully!", video_title, download_data
            return False, "Download incomplete or file not found.", None, None

    except Exception as e:
        error_msg = handle_download_error(str(e))
        if error_msg:
            return False, error_msg, None, None
        return False, str(e), None, None


def render_ui():
    """Render the main user interface."""
    st.title("🎥 YouTube Video Downloader")
    st.markdown(
        """
        Download your favorite YouTube videos easily!
        Just paste the video URL below and press Enter or click Download.
        The video will be available for download after processing.
        """
    )

    # Create a form to handle Enter key submission
    with st.form(key='download_form'):
        url = st.text_input(
            "Enter YouTube URL:", 
            placeholder="https://www.youtube.com/watch?v=..."
        )
        col1, col2 = st.columns([3, 1])
        with col1:
            submit_button = st.form_submit_button(
                "Download Video",
                type="primary",
                disabled=st.session_state.downloading
            )

    # Stop button outside the form
    stop_button_container = col2.empty()
    if st.session_state.downloading:
        if stop_button_container.button(
            "🛑 Stop",
            type="secondary",
            key="stop_button",
            class_name="stop-button"
        ):
            st.session_state.downloading = False
            st.error("Stopping download...")
            time.sleep(1)
            st.rerun()

    return url, submit_button, stop_button_container


def main():
    """Main application entry point."""
    init_session_state()
    setup_page()

    url, start_download, stop_button_container = render_ui()

    if start_download:
        if not url:
            st.error("Please enter a YouTube URL!")
        else:
            success, message, video_title, download_data = download_video(url, stop_button_container)
            if success:
                st.success(message)
                st.balloons()  # Celebration effect!
                
                # Create download button for the video
                if download_data and video_title:
                    filename = f"{video_title}.mp4"
                    st.download_button(
                        label="📥 Download Video",
                        data=download_data,
                        file_name=filename,
                        mime="video/mp4"
                    )
            else:
                st.error(message)

    st.markdown("---")
    st.markdown("Made by Shireen with ❤️ using Streamlit and yt-dlp")


if __name__ == "__main__":
    main()

import os
import tempfile
import time
from pathlib import Path

import streamlit as st
import yt_dlp

# Constants
VIDEO_FORMATS = [("MP4 files", "*.mp4"), ("MP3 files", "*.mp3")]
DEFAULT_DOWNLOAD_DIR = str(Path.home() / "Downloads")

# Format configurations
FORMAT_CONFIGS = {
    "mp4": {"format": "best", "postprocessors": []},
    "mp3": {
        "format": "best",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
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


def init_session_state():
    """Initialize Streamlit session state variables."""
    if "downloading" not in st.session_state:
        st.session_state.downloading = False
    if "download_data" not in st.session_state:
        st.session_state.download_data = None
    if "selected_format" not in st.session_state:
        st.session_state.selected_format = "mp4"


def setup_page():
    """Configure the Streamlit page settings."""
    st.set_page_config(page_title="YouTube Downloader", page_icon="", layout="centered")
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
                downloaded = d.get("downloaded_bytes", 0)
                total = d.get("total_bytes", 0) or d.get("total_bytes_estimate", 0)

                if total > 0:
                    percent = min(100.0, (downloaded / total) * 100)
                    progress_bar.progress(percent / 100)

                    # Format downloaded size
                    downloaded_mb = downloaded / (1024 * 1024)
                    total_mb = total / (1024 * 1024)
                    status = f"Downloading: {percent:.1f}% ({downloaded_mb:.1f}MB of {total_mb:.1f}MB)"
                    status_text.text(status)

            except (ValueError, AttributeError, ZeroDivisionError) as e:
                st.error(f"Error calculating progress: {str(e)}")
                pass

            temp_file_path = d.get("filename")
            video_title = d.get("info_dict", {}).get("title", "video")

        elif d["status"] == "finished":
            status_text.text("Download completed! Processing video...")
            progress_bar.progress(1.0)
            download_complete = True

            # Read the file data for download
            if temp_file_path and os.path.exists(temp_file_path):
                with open(temp_file_path, "rb") as f:
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
            progress_hook, get_download_info = create_progress_hook(
                progress_bar, status_text
            )

            # Get format configuration based on user selection
            format_config = FORMAT_CONFIGS[st.session_state.selected_format]

            ydl_opts = {
                "format": format_config["format"],
                "outtmpl": os.path.join(temp_dir, "%(title)s.%(ext)s"),
                "progress_hooks": [progress_hook],
                "postprocessors": format_config["postprocessors"],
            }

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    video_title = info.get("title", "video")
                    # Sanitize the video title to remove problematic characters
                    video_title = "".join(
                        c for c in video_title if c not in r'<>:"/\|?*'
                    )
                    status_text.text(f"Starting download of: {video_title}")
                    ydl.download([url])
            except Exception as e:
                if str(e) == "Download cancelled by user":
                    status_text.text("Download cancelled")
                    progress_bar.empty()
                    return False, "Download cancelled by user.", None, None
                raise e
            finally:
                st.session_state.downloading = False

            video_title, download_complete, download_data = get_download_info()

            if download_complete and download_data:
                return (
                    True,
                    "Video downloaded successfully!",
                    video_title,
                    download_data,
                )
            return False, "Download incomplete or file not found.", None, None

    except Exception as e:
        error_msg = handle_download_error(str(e))
        if error_msg:
            return False, error_msg, None, None
        return False, str(e), None, None


def render_header():
    """Render the application header with description."""
    st.markdown(
        """
    ### Transform YouTube Videos into MP3/MP4 Files
    This tool allows you to easily download YouTube videos in either video (MP4) or audio (MP3) format.
    Simply paste the video URL below and choose your preferred format.
    """
    )


def render_ui():
    """Render the main user interface."""
    render_header()

    with st.container():
        # URL input with validation
        url = st.text_input(
            "Enter YouTube URL:",
            placeholder="https://www.youtube.com/watch?v=...",
            key="url_input",
        )

        col1, col2 = st.columns([1, 1])

        with col1:
            format_option = st.selectbox(
                "Select Format:", ["MP4 (Video)", "MP3 (Audio)"], key="format_option"
            )
            if format_option == "MP4 (Video)":
                st.session_state.selected_format = "mp4"
            else:
                st.session_state.selected_format = "mp3"

        with col2:
            quality_option = st.selectbox(
                "Select Quality:", ["High", "Medium", "Low"], key="quality_option"
            )

        # Create columns for the download button and stop button
        button_col1, button_col2 = st.columns([3, 1])

        with button_col1:
            # Download button with custom styling
            if st.button("Download", key="download_button"):
                if not url:
                    show_error_message("Please enter a YouTube URL")
                    return

                # Progress indicators right after the button
                progress_bar = st.progress(0)
                status_text = st.empty()

                try:
                    success, message, video_title, download_data = download_video(
                        url, button_col2
                    )

                    if success:
                        show_success_message("Download completed successfully!")

                        # Create download button for the video with consistent styling
                        if download_data and video_title:
                            filename = f"{video_title}.{'mp4' if st.session_state.selected_format == 'mp4' else 'mp3'}"
                            # Create a container for the Save File button to keep it in place
                            save_container = st.container()
                            with save_container:
                                st.download_button(
                                    label="Save File",
                                    data=download_data,
                                    file_name=filename,
                                    mime=f"{'video/mp4' if st.session_state.selected_format == 'mp4' else 'audio/mpeg'}",
                                    key="save_button",
                                )
                    else:
                        show_error_message(f"{message}")
                except Exception as e:
                    show_error_message(f"An error occurred: {str(e)}")

    # Add spacer before footer
    st.markdown("<div style='margin-bottom: 80px'></div>", unsafe_allow_html=True)

    # Add footer with version info
    st.markdown(
        """
        <div class='footer'>
            <p>Version 1.0.0 | Made with ❤️ by Shireen Low</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_success_message(message):
    """Display a custom styled success message."""
    st.markdown(f'<div class="success-message">{message}</div>', unsafe_allow_html=True)


def show_error_message(message):
    """Display a custom styled error message."""
    st.markdown(f'<div class="error-message">{message}</div>', unsafe_allow_html=True)


def main():
    """Main application entry point."""
    setup_page()
    init_session_state()

    render_ui()


if __name__ == "__main__":
    main()

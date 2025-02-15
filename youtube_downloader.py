import os
import shutil
import tempfile
import time
import tkinter as tk
from tkinter import filedialog
from pathlib import Path
import streamlit as st
import yt_dlp

# Constants
DEFAULT_DOWNLOAD_DIR = str(Path.home() / "Downloads")
VIDEO_FORMATS = [("MP4 files", "*.mp4"), ("All files", "*.*")]
CUSTOM_CSS = """
    <style>
    .stProgress > div > div > div > div {
        background-color: #ff0000;
    }
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
    if "download_path" not in st.session_state:
        st.session_state.download_path = DEFAULT_DOWNLOAD_DIR
    if "tk_root" not in st.session_state:
        st.session_state.tk_root = None


def setup_page():
    """Configure the Streamlit page settings."""
    st.set_page_config(
        page_title="YouTube Video Downloader", page_icon="🎥", layout="centered"
    )
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def create_tk_root():
    """Create and configure a new Tkinter root window."""
    try:
        if st.session_state.tk_root is not None:
            st.session_state.tk_root.destroy()
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        st.session_state.tk_root = root
    except Exception:
        pass


def get_save_path(suggested_filename):
    """
    Get the save path for the downloaded video.

    Args:
        suggested_filename (str): Default filename for the video

    Returns:
        str or None: Selected file path or None if cancelled
    """
    try:
        create_tk_root()
        root = st.session_state.tk_root

        if root is None:
            default_path = Path(st.session_state.download_path) / suggested_filename
            return str(default_path)

        file_path = filedialog.asksaveasfilename(
            initialdir=st.session_state.download_path,
            initialfile=suggested_filename,
            defaultextension=".mp4",
            filetypes=VIDEO_FORMATS,
            parent=root,
        )

        if file_path:
            # Convert to Path object to handle Unicode paths properly
            path_obj = Path(file_path)
            st.session_state.download_path = str(path_obj.parent)
            return str(path_obj)
        return None
    except Exception as e:
        st.error(f"Error in file path handling: {str(e)}")
        default_path = Path(st.session_state.download_path) / suggested_filename
        return str(default_path)


def create_progress_hook(progress_bar, status_text):
    """Create a progress hook for tracking download progress."""
    temp_file_path = None
    video_title = None
    download_complete = False

    def progress_hook(d):
        nonlocal temp_file_path, video_title, download_complete

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

    return progress_hook, lambda: (temp_file_path, video_title, download_complete)


def handle_download_error(error):
    """Convert technical error messages to user-friendly ones."""
    error_msg = str(error)
    if "HTTP Error 404" in error_msg:
        return "Video not found. Please check if the URL is correct."
    if "Video unavailable" in error_msg:
        return "This video is not available. It might be private or deleted."
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
        tuple: (success, message, file_path)
    """
    try:
        st.session_state.downloading = True

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
                    return False, "Download cancelled by user.", None
                raise e
            finally:
                st.session_state.downloading = False

            temp_file_path, _, download_complete = get_status()

            if download_complete and temp_file_path and os.path.exists(temp_file_path):
                save_path = get_save_path(f"{video_title}.mp4")
                
                if save_path:
                    # Convert to Path objects for proper Unicode handling
                    save_path = Path(save_path)
                    save_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(temp_file_path, str(save_path))
                    
                    # Update the file's timestamp to current time
                    current_time = time.time()
                    os.utime(str(save_path), (current_time, current_time))
                    
                    return True, "Video downloaded successfully!", str(save_path)
                return False, "Download cancelled by user.", None
            return False, "Download incomplete or file not found.", None

    except Exception as e:
        st.session_state.downloading = False
        error_msg = handle_download_error(e)
        if error_msg is None:  # Special case for tkinter error
            return True, "Video downloaded successfully!", temp_file_path
        return False, error_msg, None


def render_ui():
    """Render the main user interface."""
    st.title("🎥 YouTube Video Downloader")
    st.markdown(
        """
        Download your favorite YouTube videos easily!
        Just paste the video URL below and press Enter or click Download.
        You'll be prompted to choose where to save the file.
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
            success, message, file_path = download_video(url, stop_button_container)
            if success:
                st.success(message)
                st.balloons()  # Celebration effect!
                if file_path:
                    st.info(f"📁 File saved at: {file_path}")
            else:
                st.error(message)

    st.markdown("---")
    st.markdown("Made by Shireen with ❤️ using Streamlit and yt-dlp")


if __name__ == "__main__":
    main()

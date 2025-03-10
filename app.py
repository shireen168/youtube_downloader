"""Streamlit UI manager for the YouTube Downloader."""

from typing import Optional, Tuple

import streamlit as st

from config import CUSTOM_CSS
from yt_video_handler import YouTubeDownloader


class UIManager:
    """Manages the Streamlit UI components and state."""

    def __init__(self):
        """Initialize the UI manager."""
        self.downloader = YouTubeDownloader()
        st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
        self.init_session_state()

    @staticmethod
    def init_session_state():
        """Initialize Streamlit session state variables."""
        if "downloading" not in st.session_state:
            st.session_state.downloading = False
        if "download_data" not in st.session_state:
            st.session_state.download_data = None
        if "selected_format" not in st.session_state:
            st.session_state.selected_format = "mp4"
        if "current_video" not in st.session_state:
            st.session_state.current_video = ""
        if "total_videos" not in st.session_state:
            st.session_state.total_videos = 0
        if "progress_placeholder" not in st.session_state:
            st.session_state.progress_placeholder = None
        if "status_placeholder" not in st.session_state:
            st.session_state.status_placeholder = None

    @staticmethod
    def show_success_message(message: str):
        """Display a custom styled success message."""
        st.markdown(
            f'<div class="success-message">{message}</div>', unsafe_allow_html=True
        )

    @staticmethod
    def show_error_message(message: str):
        """Display a custom styled error message."""
        st.markdown(
            f'<div class="error-message">{message}</div>', unsafe_allow_html=True
        )

    def render_header(self):
        """Render the application header."""
        st.markdown("# ▶️ YouTube Downloader")
        st.markdown(
            "This tool allows you to easily download YouTube videos in either video (MP4) or audio (MP3) format. "
            "Simply paste the video URL below and choose your preferred format."
        )

    def handle_download(
        self, url: str
    ) -> Tuple[bool, Optional[str], Optional[str], Optional[bytes]]:
        """Handle the download process and return results."""
        if not url:
            self.show_error_message("Please enter a YouTube URL")
            return False, None, None, None

        # Reset session state
        st.session_state.downloading = False
        st.session_state.download_data = None
        st.session_state.current_video = ""
        st.session_state.total_videos = 0

        # Start download
        return self.downloader.download(
            url,
            st.session_state.selected_format,
            st.session_state.progress_placeholder,
            st.session_state.status_placeholder,
        )

    def create_download_button(
        self, title: str, download_data: bytes, is_playlist: bool
    ):
        """Create a download button with appropriate filename and mime type."""
        if is_playlist:
            filename = f"{title}.zip"
            mime = "application/zip"
        else:
            ext = "mp4" if st.session_state.selected_format == "mp4" else "mp3"
            filename = f"{title}.{ext}"
            mime = f"{'video/mp4' if ext == 'mp4' else 'audio/mpeg'}"

        st.download_button(
            label="💾 Save File",
            data=download_data,
            file_name=filename,
            mime=mime,
            key="save_button",
        )

    def render_ui(self):
        """Render the main user interface components."""
        self.render_header()

        with st.container():
            # URL input
            url = st.text_input(
                "Enter YouTube URL (video or playlist):", key="url_input"
            )

            # Format selection
            format_col, progress_col = st.columns([1, 3])

            with format_col:
                st.session_state.selected_format = st.radio(
                    "Select Format:",
                    ["mp4", "mp3"],
                    horizontal=True,
                    key="format_radio",
                )

            with progress_col:
                # Create placeholder for progress info
                if "progress_placeholder" not in st.session_state:
                    st.session_state.progress_placeholder = st.empty()
                if "status_placeholder" not in st.session_state:
                    st.session_state.status_placeholder = st.empty()

            # Download and Stop buttons
            download_col, stop_col = st.columns([3, 1])

            with download_col:
                if st.button("⬇️ Download", key="download_button", type="primary"):
                    success, message, title, download_data = self.handle_download(url)

                    if success and download_data:
                        is_playlist = self.downloader.is_playlist_url(url)
                        self.show_success_message(message)
                        self.create_download_button(title, download_data, is_playlist)
                    else:
                        self.show_error_message(message)

            with stop_col:
                if st.button("🛑 Stop", key="stop_button", type="secondary"):
                    st.session_state.downloading = False
                    self.show_error_message("Download cancelled by user")

            # Footer
            st.markdown(
                """
                <div class="footer">
                    <p>Made with ❤️ by Shireen</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

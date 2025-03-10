"""Entry point for Streamlit Cloud deployment."""
import os
import sys
import streamlit as st
from app import UIManager
from config import CUSTOM_CSS

# Must be the first Streamlit command
st.set_page_config(
    page_title="YouTube Downloader",
    page_icon="⬇️",
    layout="centered"
)

# Apply custom CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

def setup_environment():
    """Set up the environment for the application."""
    # Ensure temp directory exists and is writable
    try:
        import tempfile
        temp_dir = tempfile.gettempdir()
        test_file = os.path.join(temp_dir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('test')
        os.remove(test_file)
    except Exception as e:
        st.error(f"❌ Error: Unable to write to temporary directory: {str(e)}")
        st.stop()

    # Check if ffmpeg is installed
    try:
        import ffmpeg
    except Exception as e:
        st.error("❌ Error: FFmpeg not found. Please ensure FFmpeg is installed.")
        st.stop()

def main():
    """Main application entry point."""
    try:
        # Set up environment
        setup_environment()

        # Initialize and render UI
        ui = UIManager()
        ui.render_ui()

        # Add footer
        st.markdown(
            """
            <div class="footer">
                Made with ❤️ using Streamlit and yt-dlp
            </div>
            """,
            unsafe_allow_html=True
        )
    except Exception as e:
        st.error(f"❌ An unexpected error occurred: {str(e)}")
        st.stop()

if __name__ == "__main__":
    main()

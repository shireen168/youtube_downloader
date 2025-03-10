"""Entry point for Streamlit Cloud deployment."""
import streamlit as st
from app import UIManager

# Must be the first Streamlit command
st.set_page_config(
    page_title="YouTube Downloader",
    page_icon="⬇️",
    layout="centered"
)

def main():
    """Main application entry point."""
    ui = UIManager()
    ui.render_ui()

if __name__ == "__main__":
    main()

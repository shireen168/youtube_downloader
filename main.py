"""Main entry point for the YouTube Downloader application."""

from app import UIManager


def main():
    """Main application entry point."""
    ui = UIManager()
    ui.render_ui()


if __name__ == "__main__":
    main()

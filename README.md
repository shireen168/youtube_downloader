# YouTube Downloader

A modern Streamlit application to download YouTube videos and playlists using yt-dlp.

## Features

- 📺 Download single videos or entire playlists
- 🎵 Support for both MP4 (video) and MP3 (audio) formats
- 📊 Real-time progress tracking with percentage and size display
- 📦 Playlist downloads are automatically packaged as ZIP files
- 🎨 Modern, user-friendly interface with emoji-enhanced buttons
- ⚡ Fast downloads using yt-dlp

## Project Structure

```
youtube_downloader/
├── main.py          # Application entry point
├── app.py           # Streamlit UI components and layout
├── config.py        # Configuration settings and styling
├── yt_video_handler.py  # YouTube download functionality
└── requirements.txt # Project dependencies
```

## Prerequisites

- Python 3.x
- Poetry (Python package manager)

## Setup Instructions

1. Clone this repository:
```bash
git clone https://github.com/shireen168/youtube_downloader.git
cd youtube_downloader
```

2. Install dependencies using Poetry:
```bash
poetry install
```

## Usage

1. Run the application:
```bash
poetry run streamlit run main.py
```

2. Open your web browser to the displayed URL (typically http://localhost:8501)

3. Enter a YouTube URL (video or playlist)

4. Select your preferred format (MP4 or MP3)

5. Click the Download button

6. Once the download is complete, click "Save File" to save your video/audio

## Development

The application is built with:
- Streamlit for the web interface
- yt-dlp for YouTube video processing
- Poetry for dependency management

To modify the application:
- UI components are in `app.py`
- Download logic is in `yt_video_handler.py`
- Configuration settings are in `config.py`
- Main entry point is `main.py`

## Contributing

Feel free to open issues or submit pull requests for any improvements.

## License

This project is open source and available under the MIT License.

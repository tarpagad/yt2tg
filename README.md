# YouTube Telegram Uploader

A Python script to download audio from a YouTube video, convert it to MP3, and upload it to a Telegram channel with metadata and an optional thumbnail.

## Features

- Downloads audio from YouTube videos using `yt-dlp`.
- Converts audio to MP3 with a configurable bitrate.
- Cleans video titles for safe filenames and Telegram metadata.
- Uploads audio to a specified Telegram channel with title, performer, duration, and source URL.
- Supports optional thumbnail upload.
- Manages temporary files with robust cleanup.
- Configurable via environment variables for security and flexibility.

## Prerequisites

- **Python 3.7 or higher**: Check your Python version by running:
  ```bash
  python3 --version
  ```
  If Python is not installed, download it from [python.org](https://www.python.org/downloads/) or use your system’s package manager.

- **A Telegram bot token**: Obtain one from [BotFather](https://t.me/BotFather) on Telegram.
- **A Telegram channel**: Ensure your bot has permission to post in the channel.
- **FFmpeg**: A command-line tool required for audio conversion.

## Installation

Follow these steps to set up the project:

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/tarpagad/yt2tg.git
   cd yt2tg
   ```

2. **Set Up a Python Virtual Environment** (recommended to avoid conflicts):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python Packages**:
   The script requires only three external Python packages:
   ```bash
   pip install yt-dlp python-telegram-bot python-dotenv
   ```
   - `yt-dlp`: Downloads YouTube videos.
   - `python-telegram-bot`: Interacts with Telegram.
   - `python-dotenv`: Loads configuration from a `.env` file.
   - **Note**: Other required modules (e.g., `os`, `sys`, `datetime`) are part of Python’s standard library and don’t need installation.

4. **Install FFmpeg**:
   - **Ubuntu/Debian**:
     ```bash
     sudo apt update
     sudo apt install ffmpeg
     ```
   - **macOS** (using Homebrew):
     ```bash
     brew install ffmpeg
     ```
   - **Windows**:
     1. Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html) or a trusted source like [gyan.dev](https://www.gyan.dev/ffmpeg/builds/).
     2. Extract the archive and add the `bin` folder to your system PATH (search online for “add FFmpeg to PATH on Windows” for detailed steps).
     3. Verify installation:
        ```bash
        ffmpeg -version
        ```

5. **Create a `.env` File**:
   In the project root, create a file named `.env` with the following content:
   ```env
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_CHANNEL_ID=@your_channel_id_here
   VERBOSE=False
   ```
   - Replace `your_bot_token_here` with your Telegram bot token.
   - Replace `@your_channel_id_here` with your Telegram channel ID (e.g., `@MyChannel`).
   - Set `VERBOSE=True` for detailed debug output (optional, default is `False`).

6. **Verify Setup**:
   Ensure FFmpeg is installed by running:
   ```bash
   ffmpeg -version
   ```
   Check that the virtual environment is active (you should see `(venv)` in your terminal prompt).

## Usage

Run the script with a YouTube video URL as an argument:

```bash
python yt2tg.py https://www.youtube.com/watch?v=C1sAsoJVN1U
```

### What the Script Does
1. Extracts the video ID from the URL (e.g., `C1sAsoJVN1U`).
2. Downloads the best available audio and converts it to MP3.
3. Retrieves metadata (title, uploader, duration) and the video thumbnail.
4. Uploads the MP3 to your Telegram channel with a caption including the title and source URL.
5. Cleans up temporary files.

### Supported URL Formats
- Standard: `https://www.youtube.com/watch?v=video_id`
- Short: `https://youtu.be/video_id`
- URLs with extra parameters (e.g., `https://www.youtube.com/watch?v=video_id&feature=share`)

## Configuration

Customize the script using the `.env` file:
- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token (required).
- `TELEGRAM_CHANNEL_ID`: The Telegram channel ID (default: `@generalissadiawara`).
- `VERBOSE`: Set to `True` for detailed logs (default: `False`).
- `DEFAULT_MAX_ABR`: Audio bitrate in kbps (default: `192`).

## File Structure

```plaintext
yt2tg/
├── yt2tg.py  # Main script
├── .env                         # Environment variables (not tracked in git)
├── README.md                    # This file
├── LICENSE.md                   #
└── .gitignore                   # Git ignore file
```

## Security Notes

- **Protect Your `.env` File**: Add `.env` to `.gitignore` to prevent exposing your Telegram bot token. Example `.gitignore`:
  ```gitignore
  .env
  venv/
  __pycache__/
  *.mp3
  *.jpg
  *.webp
  *.png
  *.jpeg
  ```
- **Bot Permissions**: Ensure your bot is added to the Telegram channel with posting permissions.
- **Rate Limits**: Avoid excessive uploads to prevent Telegram API rate limit issues.

## Troubleshooting for Beginners

- **“Command not found: python3”**:
  - Ensure Python 3 is installed. Run `python3 --version` or `python --version`. Install Python from [python.org](https://www.python.org/downloads/) if needed.
- **“Module not found” errors**:
  - Ensure you’re in the virtual environment (`source venv/bin/activate` or `venv\Scripts\activate` on Windows).
  - Reinstall packages: `pip install yt-dlp python-telegram-bot python-dotenv`.
- **“FFmpeg not found”**:
  - Verify FFmpeg installation with `ffmpeg -version`.
  - Ensure FFmpeg is in your system PATH (especially on Windows).
- **“Could not extract video ID from URL”**:
  - Check that the URL is a valid YouTube video URL.
- **“Telegram API error”**:
  - Verify your bot token and channel ID in the `.env` file.
  - Ensure the bot is an admin in the channel with posting permissions.
- **Still stuck?**:
  - Set `VERBOSE=True` in `.env` and rerun the script to see detailed logs.
  - Search for the error message online or open an issue on GitHub.

## Contributing

Contributions are welcome! To contribute:
1. Fork the repository.
2. Create a branch (`git checkout -b feature/your-feature`).
3. Make changes and commit (`git commit -m "Add your feature"`).
4. Push to your branch (`git push origin feature/your-feature`).
5. Open a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp) for YouTube audio extraction.
- Uses [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) for Telegram integration.
- Leverages [python-dotenv](https://github.com/theskumar/python-dotenv) for configuration management.

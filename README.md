# YouTube Telegram Uploader

A Python script to download audio from YouTube videos, convert it to MP3, and upload it to a Telegram channel with metadata and an optional thumbnail. Includes a monitoring script to automatically detect and process new videos from a specified YouTube channel.

## Features

- Downloads audio from YouTube videos using `yt-dlp`.
- Converts audio to MP3 with a configurable bitrate.
- Cleans video titles for safe filenames and Telegram metadata.
- Uploads audio to a specified Telegram channel with title, performer, duration, and source URL.
- Supports optional thumbnail upload.
- Monitors a YouTube channel for new videos via RSS feed and triggers uploads automatically.
- Configurable via environment variables for security and flexibility.

## Prerequisites

- **Python 3.7 or higher**: Check your Python version by running:
  ```bash
  python3 --version
  ```
  If Python is not installed, download it from [python.org](https://www.python.org/downloads/) or use your system’s package manager.

- **A Telegram bot token**: Obtain one from [BotFather](https://t.me/BotFather) on Telegram.
- **A Telegram channel**: Ensure your bot has permission to post in the channel.
- **A YouTube channel ID**: Find it by viewing the channel’s page source and searching for `"channel_id"` (e.g., `UC_x5XG1OV2P6uZZ5FSM9Ttw`) or use an online tool like [TunePocket YouTube Channel ID Finder](https://www.tunepocket.com/youtube-channel-id-finder/).
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
   The project requires four external Python packages:
   ```bash
   pip install yt-dlp python-telegram-bot python-dotenv feedparser
   ```
   - `yt-dlp`: Downloads YouTube videos.
   - `python-telegram-bot`: Interacts with Telegram.
   - `python-dotenv`: Loads configuration from a `.env` file.
   - `feedparser`: Parses YouTube RSS feeds for monitoring.
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
   YOUTUBE_CHANNEL_ID=your_youtube_channel_id_here
   VERBOSE=False
   ```
   - Replace `your_bot_token_here` with your Telegram bot token.
   - Replace `@your_channel_id_here` with your Telegram channel ID (e.g., `@MyChannel`).
   - Replace `your_youtube_channel_id_here` with the YouTube channel ID (e.g., `UC_x5XG1OV2P6uZZ5FSM9Ttw`).
   - Set `VERBOSE=True` for detailed debug output (optional, default is `False`).

6. **Verify Setup**:
   Ensure FFmpeg is installed by running:
   ```bash
   ffmpeg -version
   ```
   Check that the virtual environment is active (you should see `(venv)` in your terminal prompt).

## Usage

### Manual Upload
Run the uploader script with a YouTube video URL as an argument:
```bash
python yt2tg.py https://www.youtube.com/watch?v=C1sAsoJVN1U
```

### Automated Monitoring
Run the monitoring script to check for new videos on the specified YouTube channel:
```bash
python yt-monitor.py
```
- The script checks the channel’s RSS feed, detects new videos, and runs the uploader script for each one.
- It stores the last processed video’s timestamp in `last_seen.json` to avoid duplicates.

### Scheduling Automation
To run the monitoring script automatically (e.g., every 15 minutes):
- **Linux/macOS (Cron)**:
  1. Open crontab: `crontab -e`.
  2. Add:
     ```cron
     */15 * * * * /path/to/venv/bin/python /path/to/yt2tg/yt-monitor.py >> /path/to/log.txt 2>&1
     ```
     - Replace `/path/to/venv/bin/python` and `/path/to/yt2tg/yt-monitor.py` with actual paths.
     - Logs output to `log.txt` for debugging.
- **Windows (Task Scheduler)**:
  1. Open Task Scheduler from the Start menu.
  2. Create a task with a trigger (e.g., every 15 minutes).
  3. Set action: Start a program → `C:\path\to\python.exe`.
  4. Add arguments: `C:\path\to\yt-monitor.py`.
  5. Set “Start in”: The project directory.
  6. Enable “Run whether user is logged on or not.”

## Configuration

Customize the project using the `.env` file:
- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token (required).
- `TELEGRAM_CHANNEL_ID`: The Telegram channel ID (default: `@generalissadiawara`).
- `YOUTUBE_CHANNEL_ID`: The YouTube channel ID to monitor (e.g., `UC_x5XG1OV2P6uZZ5FSM9Ttw`).
- `VERBOSE`: Set to `True` for detailed logs (default: `False`).
- `DEFAULT_MAX_ABR`: Audio bitrate in kbps (default: `192`).

## File Structure

```plaintext
yt2tg/
├── youtube_telegram_uploader.py  # Main uploader script
├── yt-monitor.py    # Monitoring script for new videos
├── .env                         # Environment variables (not tracked in git)
├── last_seen.json               # Stores last processed video timestamp
├── README.md                    # This file
├── LICENSE                      # MIT License
└── .gitignore                   # Git ignore file
```

## Security Notes

- **Protect Your `.env` File**: Add `.env` to `.gitignore` to prevent exposing sensitive data. Example `.gitignore`:
  ```gitignore
  .env
  venv/
  __pycache__/
  last_seen.json
  *.mp3
  *.jpg
  *.webp
  *.png
  *.jpeg
  ```
- **Bot Permissions**: Ensure your bot is an admin in the Telegram channel with posting permissions.
- **Rate Limits**: Avoid excessive uploads to prevent Telegram API rate limit issues.

## Troubleshooting for Beginners

- **“Command not found: python3”**:
  - Ensure Python 3 is installed: `python3 --version`. Install from [python.org](https://www.python.org/downloads/) if needed.
- **“Module not found” errors**:
  - Activate the virtual environment: `source venv/bin/activate` (or `venv\Scripts\activate` on Windows).
  - Reinstall packages: `pip install yt-dlp python-telegram-bot python-dotenv feedparser`.
- **“FFmpeg not found”**:
  - Verify FFmpeg: `ffmpeg -version`.
  - Ensure FFmpeg is in your system PATH (especially on Windows).
- **“YOUTUBE_CHANNEL_ID not set”**:
  - Check that `YOUTUBE_CHANNEL_ID` is in the `.env` file and matches the channel’s ID.
- **“Error parsing feed”**:
  - Verify the `YOUTUBE_CHANNEL_ID` is correct. Test the RSS URL (`https://www.youtube.com/feeds/videos.xml?channel_id=ID`) in a browser.
- **“Telegram API error”**:
  - Confirm bot token and channel ID in `.env`.
  - Ensure the bot has posting permissions.
- **Still stuck?**:
  - Set `VERBOSE=True` in `.env` and rerun to see detailed logs.
  - Search the error online or open a GitHub issue.

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
- Leverages [python-dotenv](https://github.com/theskumar/python-dotenv) for configuration.
- Uses [feedparser](https://github.com/kurtmckee/feedparser) for RSS feed parsing.

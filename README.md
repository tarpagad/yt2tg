# YouTube to Telegram Feed Monitor

This application monitors a YouTube channel's RSS feed for new videos, downloads the audio (MP3) using `yt-dlp`, and uploads it to a specified Telegram channel. It is designed to run locally, spawning a terminal window for the download process to keep the main application lightweight and responsive.

## Features

- **RSS Monitoring**: checks for new videos based on the `pubDate`.
- **Automated Download**: Spawns a dedicated terminal window to run `yt-dlp`.
- **Telegram Integration**: Uploads the downloaded MP3 to a Telegram channel with metadata.
- **State Management**: Keeps track of the last processed video in `last_seen.json`.
- **Smart Cleanup**: Deletes local files after successful upload.

## Prerequisites

- Python 3.8+
- `ffmpeg` (required by yt-dlp for audio conversion)
- `yt-dlp` (installed via pip)

## Installation

1. Clone the repository or download the source code.
2. Create a virtual environment (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: valid `requirements.txt` should include: `feedparser`, `python-telegram-bot`, `python-dotenv`, `yt-dlp`)*

## Configuration

Create a `.env` file in the project root with the following variables:

```ini
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHANNEL_ID=your_channel_id_here
YOUTUBE_CHANNEL_ID=your_youtube_channel_id_here
```

## Usage

### Running form Source

```bash
python3 yt2tg.py
```

### Compiling with PyInstaller

You can compile the script into a standalone executable using `pyinstaller`. A spec file `yt2tg.spec` is provided.

1. Install PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Build the executable:
   ```bash
   pyinstaller yt2tg.spec
   ```
   Or manually:
   ```bash
   pyinstaller --onefile --name yt2tg yt2tg.py
   ```

3. The executable will be located in the `dist/` folder:
   ```bash
   ./dist/yt2tg
   ```

## How it works

1. **Feed Check**: The script fetches the RSS feed for the configured YouTube channel.
2. **New Video Detection**: It compares the publication date of videos against the timestamp stored in `last_seen.json`.
3. **Download**:
   - For each new video, it spawns a visible terminal window.
   - `yt-dlp` runs in this window to download and convert the video to MP3.
   - The terminal closes automatically upon completion.
4. **Upload**: If the download was successful, the bot uploads the audio file to Telegram.
5. **Update State**: The `last_seen.json` file is updated only after a successful upload.

## Troubleshooting

- **Terminal not opening**: Ensure you have a supported terminal emulator installed (gnome-terminal, xfce4-terminal, konsole, xterm).
- **Download fails**: Check `yt2tg_monitor.log` or the brief output in the spawned terminal. Ensure `ffmpeg` is installed.

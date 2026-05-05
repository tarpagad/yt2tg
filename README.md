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

---

## Railway Deployment

This project supports deployment to [Railway.app](https://railway.app) for fully automated, daily execution without manual intervention.

### Branch

The Railway-compatible version is on the `railway-deploy` branch. It removes all interactive terminal spawning and runs non-interactively.

### Quick Setup

1. **Deploy from GitHub**:
   - Push the `railway-deploy` branch to your repository
   - In Railway, create a new project and select "Deploy from GitHub"
   - Choose the `railway-deploy` branch

2. **Set Service Type to Cron**:
   - Open your service → **Settings** → **Service Type** → Select **Cron**
   - This enables the Cron Schedule setting

3. **Configure Cron Schedule**:
   - Go to **Settings** → **Cron Schedule**
   - Set your desired schedule (e.g., `0 9 * * *` for daily at 9 AM UTC)
   - Set **Command** to `python yt2tg.py`

4. **Add Environment Variables** (in Railway Variables tab):
   | Variable | Description |
   |---|---|
   | `TELEGRAM_BOT_TOKEN` | Your Telegram bot token |
   | `TELEGRAM_CHANNEL_ID` | Your Telegram channel ID |
   | `YOUTUBE_CHANNEL_ID` | The YouTube channel ID to monitor |
   | `DATA_DIR` | Persistent storage path (default: `/data`) |

5. **Attach Persistent Storage** (required):
   - Go to **Storage** → **Add Volume**
   - Mount the volume at `/data`
   - This ensures `last_seen.json` persists between cron runs

### How It Works on Railway

- **Build**: Railpack detects Python from `requirements.txt` and installs `ffmpeg` as a system dependency via `railpack.json`
- **Run**: The script runs once per cron trigger, checks for new videos, downloads them, uploads to Telegram, and exits
- **State**: `last_seen.json` and logs are stored in `/data` (your persistent volume)
- **Cleanup**: Downloaded MP3 files are deleted after successful upload to save space

### Configuration Files

| File | Purpose |
|---|---|
| `railway.json` | Railway service configuration (builder, env vars) |
| `railpack.json` | Railpack config for system dependencies (ffmpeg) |
| `Procfile` | Defines the start command |

### Important Notes

- The Railway version downloads and processes videos **automatically** without user confirmation
- Without a persistent volume at `/data`, the `last_seen.json` file will be lost between runs, causing duplicate uploads
- Logs are written to `/data/yt2tg_monitor.log` for debugging via Railway's log viewer

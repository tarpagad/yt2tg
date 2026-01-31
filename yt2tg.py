#!/usr/bin/env python3
"""
YouTube to Telegram Feed Monitor
Monitors a YouTube RSS feed, prompts user to download new videos in a terminal,
and uploads them to Telegram.
"""

import os
import sys
import asyncio
import subprocess
import tempfile
import shutil
import time
import json
import logging
import platform
from datetime import datetime
from dotenv import load_dotenv

import feedparser
import telegram
from telegram.constants import ParseMode

# --- Configuration ---
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('yt2tg_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
LAST_SEEN_FILE = "last_seen.json"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID")

class FeedMonitor:
    def __init__(self):
        self.verify_config()
        self.base_dir = os.path.dirname(os.path.abspath(__file__))

    def verify_config(self):
        if not all([TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID, YOUTUBE_CHANNEL_ID]):
            logger.error("Missing configuration. Please check .env file.")
            logger.error("Required: TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID, YOUTUBE_CHANNEL_ID")
            sys.exit(1)

    def load_last_seen(self):
        """Load the timestamp of the last processed video."""
        if os.path.exists(LAST_SEEN_FILE):
            try:
                with open(LAST_SEEN_FILE, "r") as f:
                    data = json.load(f)
                    # Handle ISO format with timezone
                    return datetime.fromisoformat(data["last_published"])
            except Exception as e:
                logger.error(f"Error loading last_seen.json: {e}")
                return None
        return None

    def save_last_seen(self, timestamp):
        """Save the timestamp of the last processed video."""
        try:
            with open(LAST_SEEN_FILE, "w") as f:
                json.dump({"last_published": timestamp.isoformat()}, f)
        except Exception as e:
            logger.error(f"Error saving last_seen.json: {e}")

    def get_new_videos(self):
        """Fetch RSS feed and filter new videos."""
        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={YOUTUBE_CHANNEL_ID}"
        logger.info(f"Checking feed: {rss_url}")
        
        feed = feedparser.parse(rss_url)
        if feed.bozo:
            logger.error(f"Error parsing feed: {feed.bozo_exception}")
            return []

        last_seen = self.load_last_seen()
        new_videos = []

        logger.info(f"Last seen timestamp: {last_seen}")

        for entry in feed.entries:
            # Entry published format: 2023-10-27T10:00:00+00:00
            try:
                published = datetime.fromisoformat(entry.published)
            except ValueError:
                # Fallback if format is different
                published = datetime.strptime(entry.published, "%Y-%m-%dT%H:%M:%S%z")

            if last_seen is None or published > last_seen:
                new_videos.append({
                    'id': entry.yt_videoid,
                    'title': entry.title,
                    'link': entry.link,
                    'published': published,
                    'author': entry.author
                })

        # Sort by published date (oldest first) so we process in order
        new_videos.sort(key=lambda x: x['published'])
        return new_videos

    def clean_filename(self, title):
        """Creates a safe filename from title."""
        # Keep alphanumeric, spaces, hyphens, underscores
        safe_chars = "".join(c for c in title if c.isalnum() or c in " -_")
        return safe_chars.strip()

    def spawn_download_terminal(self, video, dest_dir):
        """
        Spawns a new terminal window that:
        1. Shows the yt-dlp command
        2. Waits for user confirmation (Enter)
        3. Waits for user to close/finish
        4. Returns exit code
        """
        system = platform.system()
        
        # We enforce a clean filename to ensure we know where it lands
        clean_name = self.clean_filename(video['title'])
        # limited length
        if len(clean_name) > 100:
            clean_name = clean_name[:100]
            
        # Output template (relative)
        output_template = f"{clean_name}.%(ext)s"
        
        # Expected final filename (after MP3 conversion)
        expected_filename = f"{clean_name}.mp3"
        expected_path = os.path.join(dest_dir, expected_filename)
        
        # Base yt-dlp command
        yt_cmd = [
            "yt-dlp",
            "-x", # Audio only
            "--audio-format", "mp3", 
            "--audio-quality", "0",
            "-o", output_template,
            video['link']
        ]
        
        import shlex
        cmd_str = shlex.join(yt_cmd)
        
        logger.info(f"Preparing to download: {video['title']}")
        
        if system == "Linux":
            venv_activation = ""
            if os.environ.get("VIRTUAL_ENV"):
                venv_path = os.environ.get("VIRTUAL_ENV")
                activate_script = os.path.join(venv_path, "bin", "activate")
                if os.path.exists(activate_script):
                     venv_activation = f"source {shlex.quote(activate_script)}"

            # Wrapper script
            script_content = f"""#!/bin/bash
{venv_activation}

echo "=================================================="
echo "Video: {video['title']}"
echo "URL:   {video['link']}"
echo "=================================================="
echo ""
echo "Command to run:"
echo "{cmd_str}"
echo ""

echo "Starting download..."
# Ensure we run from the destination directory (HOME)
cd {shlex.quote(dest_dir)}

{cmd_str}
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "Download Success!"
else
    echo "Download Failed! Code: $EXIT_CODE"
fi

exit $EXIT_CODE
"""
            script_fd, script_path = tempfile.mkstemp(suffix=".sh", prefix="yt2tg_")
            with os.fdopen(script_fd, 'w') as f:
                f.write(script_content)
            os.chmod(script_path, 0o755)

            terminals = [
                ('gnome-terminal', ['--wait', '--']), 
                ('xfce4-terminal', ['--disable-server', '--wait', '-e']),
                ('konsole', ['--nofork', '-e']), 
                ('xterm', ['-e']),
                ('terminator', ['-e']),
                ('sway-terminal', ['-e'])
            ]
            
            chosen_term = None
            term_cmd = []

            for term, args in terminals:
                if shutil.which(term):
                    if term == 'gnome-terminal':
                        term_cmd = [term] + args + [script_path]
                    elif term == 'xfce4-terminal':
                         term_cmd = [term] + args + [script_path]
                    elif term == 'xterm':
                        term_cmd = [term] + args + [script_path]
                    elif term == 'konsole':
                        term_cmd = [term] + args + [f"/bin/bash {script_path}"]
                    else:
                        term_cmd = [term] + args + [script_path]
                    
                    chosen_term = term
                    break
            
            if not chosen_term:
                logger.error("No supported terminal emulator found.")
                print("No suitable terminal found to spawn. Running inline.")
                input("Press Enter to run command inline...")
                subprocess.run(["bash", script_path])
                os.remove(script_path)
                return expected_path 
            
            logger.info(f"Spawning terminal: {chosen_term}")
            
            try:
                subprocess.run(term_cmd)
            except Exception as e:
                logger.error(f"Failed to run terminal: {e}")
                os.remove(script_path)
                return None

            # Clean up script? Might wait a bit just in case? 
            # Actually if subprocess returns, script is detached or done.
            # We assume done if --wait worked.
            
            return expected_path

        else:
            logger.error(f"System {system} not fully implemented.")
            return None

    async def send_to_telegram(self, audio_path, video):
        """Uploads the file to Telegram."""
        try:
            bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
            caption = f"<strong>{video['title']}</strong>\n\n<b>Source:</b> {video['link']}"
            
            logger.info(f"Uploading {audio_path}...")
            
            with open(audio_path, 'rb') as f:
                await bot.send_audio(
                    chat_id=TELEGRAM_CHANNEL_ID,
                    audio=f,
                    caption=caption,
                    title=video['title'][:64],
                    performer=video.get('author', 'Unknown'),
                    parse_mode=ParseMode.HTML,
                    write_timeout=300,
                    connect_timeout=60
                )
            logger.info("Upload Successful.")
            return True
        except Exception as e:
            logger.error(f"Telegram upload failed: {e}")
            return False

    async def start(self):
        new_videos = self.get_new_videos()
        
        if not new_videos:
            logger.info("No new videos found.")
            return

        logger.info(f"Found {len(new_videos)} new videos.")
        
        # Destination: HOME directory
        home_dir = os.path.expanduser("~")

        for video in new_videos:
            logger.info(f"Processing: {video['title']}")
            
            # Spawn download
            expected_file = self.spawn_download_terminal(video, home_dir)

            if not expected_file:
                logger.error("Failed to initiate download.")
                continue

            # Wrapper script (non-interactive)
            print(f">>> Processing video: {video['title']}")

            
            # Verify file exists
            if os.path.exists(expected_file):
                # Upload
                success = await self.send_to_telegram(expected_file, video)
                
                if success:
                    self.save_last_seen(video['published'])
                
                # Cleanup
                try:
                    os.remove(expected_file)
                    logger.info(f"Removed local file: {expected_file}")
                except Exception as e:
                    logger.warning(f"Failed to remove {expected_file}: {e}")
            else:
                logger.warning(f"Expected file not found: {expected_file}")
                logger.warning("Perhaps the filename characters were replaced differently by yt-dlp?")
                logger.warning("Check your Home directory manually.")
            
            time.sleep(1)

def main():
    monitor = FeedMonitor()
    asyncio.run(monitor.start())

if __name__ == "__main__":
    main()

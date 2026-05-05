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
        Non-interactive download for Railway deployment.
        Downloads audio using yt-dlp directly without terminal interaction.
        """
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
        
        logger.info(f"Preparing to download: {video['title']}")
        logger.info(f"Command: {' '.join(yt_cmd)}")
        
        # Ensure we run from the destination directory
        original_dir = os.getcwd()
        try:
            os.chdir(dest_dir)
            
            # Run yt-dlp directly
            result = subprocess.run(
                yt_cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                logger.info("Download Success!")
                return expected_path
            else:
                logger.error(f"Download Failed! Code: {result.returncode}")
                logger.error(f"stderr: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error("Download timed out after 5 minutes")
            return None
        except Exception as e:
            logger.error(f"Failed to run download: {e}")
            return None
        finally:
            os.chdir(original_dir)

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

import sys
import feedparser
import json
import os
import subprocess
from datetime import datetime, timezone
from dotenv import load_dotenv
import logging

# Configure logging with timestamps
logging.basicConfig(
    level=logging.INFO,  # Set to DEBUG for more details, INFO for standard
    format='%(asctime)s - %(levelname)s - %(message)s',  # Includes timestamp, level, message
    handlers=[
        logging.FileHandler('monitor.log'),  # Write to monitor.log
        logging.StreamHandler()  # Also print to console (optional; remove if unwanted)
    ]
)
logger = logging.getLogger(__name__)  # Use this logger throughout

# Load environment variables
load_dotenv()

# Configuration
YOUTUBE_CHANNEL_ID = os.getenv("YOUTUBE_CHANNEL_ID")
if not YOUTUBE_CHANNEL_ID:
    logger.error("Error: YOUTUBE_CHANNEL_ID not set in .env file")
    sys.exit(1)
RSS_FEED_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={YOUTUBE_CHANNEL_ID}"
UPLOADER_SCRIPT = "yt2tg.py"  # Your existing script
LAST_SEEN_FILE = "last_seen.json"  # File to store the last processed timestamp

def load_last_seen():
    if os.path.exists(LAST_SEEN_FILE):
        with open(LAST_SEEN_FILE, "r") as f:
            data = json.load(f)
            return datetime.fromisoformat(data["last_published"]).replace(tzinfo=timezone.utc)
    return None  # No previous data means process all

def save_last_seen(timestamp):
    with open(LAST_SEEN_FILE, "w") as f:
        json.dump({"last_published": timestamp.isoformat()}, f)

# Fetch and parse RSS feed
feed = feedparser.parse(RSS_FEED_URL)
if feed.bozo:  # Error check
    logger.error(f"Error parsing feed: {feed.bozo_exception}")
    sys.exit(1)

last_seen = load_last_seen()
new_videos = []

# Collect new videos (entries are in reverse chronological order)
for entry in feed.entries:
    published = datetime.strptime(entry.published, "%Y-%m-%dT%H:%M:%S%z").astimezone(timezone.utc)
    if last_seen is None or published > last_seen:
        new_videos.append((published, entry.link))  # (timestamp, video URL)

if not new_videos:
    logger.info("No new videos found.")
    sys.exit(0)

# Sort by publish date (oldest first) to process in order
new_videos.sort(key=lambda x: x[0])

# Process each new video
newest_timestamp = last_seen
for published, video_url in new_videos:
    logger.info(f"New video found: {video_url}")
    try:
        subprocess.run(["python", UPLOADER_SCRIPT, video_url], check=True)
        logger.info(f"Uploaded: {video_url}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error uploading {video_url}: {e}")
    # Update newest timestamp
    if newest_timestamp is None or published > newest_timestamp:
        newest_timestamp = published

# Save the newest timestamp
if newest_timestamp:
    save_last_seen(newest_timestamp)

logger.info("Monitoring complete.")

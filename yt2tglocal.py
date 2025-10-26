#coding: utf-8
import os
import sys
import asyncio
import telegram
import subprocess
import tempfile
import shutil
import time
import urllib.parse
from datetime import datetime
import re
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

# --- CONFIGURATION ---
load_dotenv()  # Load environment variables from .env file
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Load token from environment variable
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "@generalissadiawara")  # Default channel ID

def clean_title(title):
    """
    Clean title for filename and Telegram metadata: remove invalid characters and trim to Telegram limits.
    """
    if not title:
        return "Unknown Title"
    # Remove common invalid filename characters
    title = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', str(title))
    # Trim whitespace
    title = title.strip()
    # Limit to Telegram's title/performer length (64 chars)
    title = title[:64]
    return title

def extract_video_info(video_url):
    """
    Extract video information using yt-dlp executable.
    """
    try:
        # Use yt-dlp to extract video info in JSON format
        result = subprocess.run(
            ["yt-dlp", "--dump-json", video_url],
            capture_output=True,
            text=True,
            check=True
        )
        
        import json
        info_dict = json.loads(result.stdout)
        
        return {
            'title': info_dict.get('title', 'Unknown Title'),
            'uploader': info_dict.get('uploader', 'Unknown'),
            'duration': info_dict.get('duration', 0),
            'upload_date': info_dict.get('upload_date')
        }
    except subprocess.CalledProcessError as e:
        logger.error(f"Error extracting video info: {e}")
        return None
    except Exception as e:
        logger.error(f"Error parsing video info: {e}")
        return None

async def main():
    """
    Downloads audio from a YouTube video using local yt-dlp executable as MP3, 
    and uploads it to Telegram.
    """
    if len(sys.argv) < 2:
        print("Usage: python yt2tglocal.py <youtube_video_url>")
        sys.exit(1)

    video_url = sys.argv[1]
    
    # Extract video ID from URL for filename
    parsed_url = urllib.parse.urlparse(video_url)
    video_id = None
    
    # Handle standard YouTube URLs (e.g., https://www.youtube.com/watch?v=dQw4w9WgXcQ)
    if 'v' in urllib.parse.parse_qs(parsed_url.query):
        video_id = urllib.parse.parse_qs(parsed_url.query)['v'][0]
    # Handle short YouTube URLs (e.g., https://youtu.be/dQw4w9WgXcQ)
    elif parsed_url.netloc == 'youtu.be':
        video_id = parsed_url.path.lstrip('/')
    # Handle YouTube shorts
    elif 'youtube.com/shorts' in video_url:
        video_id = parsed_url.path.split('/')[-1]
    
    if not video_id:
        logger.error("Error: Could not extract video ID from URL")
        sys.exit(1)
    
    temp_dir = None
    audio_filename = None

    try:
        # Validate Telegram bot token
        if not TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")

        # Create a temporary directory for downloads
        temp_dir = tempfile.mkdtemp()
        logger.info(f"Created temporary directory: {temp_dir}")

        # Extract video info first
        logger.info("Extracting video information...")
        video_info = extract_video_info(video_url)
        if not video_info:
            logger.error("Could not extract video information")
            sys.exit(1)
            
        title = video_info['title']
        uploader = video_info['uploader']
        duration = video_info['duration']
        
        # Clean title for filename
        clean_title_ = clean_title(title)
        
        # Set output filename pattern
        output_pattern = os.path.join(temp_dir, f"{clean_title_}.%(ext)s")
        
        # Execute yt-dlp command to download and extract audio as MP3
        logger.info(f"Downloading audio from: {video_url}")
        logger.info(f"Command: yt-dlp -x --audio-format mp3 -o \"{output_pattern}\" \"{video_url}\"")
        
        result = subprocess.run([
            "yt-dlp",
            "-x",  # Extract audio
            "--audio-format", "mp3",  # Convert to MP3
            "-o", output_pattern,  # Output filename pattern
            video_url
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"yt-dlp failed with error: {result.stderr}")
            sys.exit(1)
        
        logger.info("Download completed successfully")
        
        # Find the downloaded MP3 file
        mp3_files = [f for f in os.listdir(temp_dir) if f.lower().endswith('.mp3')]
        if not mp3_files:
            logger.error("No MP3 file found after download")
            sys.exit(1)
            
        audio_filename = os.path.join(temp_dir, mp3_files[0])
        logger.info(f"Found audio file: {audio_filename}")
        
        # Check if the file has been properly renamed to match our clean title
        expected_filename = os.path.join(temp_dir, f"{clean_title_}.mp3")
        if audio_filename != expected_filename:
            # If the filename doesn't match our expected format, rename it
            os.rename(audio_filename, expected_filename)
            audio_filename = expected_filename
            logger.info(f"Renamed audio file to: {audio_filename}")
        
        # --- Upload to Telegram ---
        logger.info("Uploading to Telegram...")
        bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

        # Prepare caption with original URL
        caption = f"<strong>{title}</strong>\n\n<b>Vidéo source:</b> {video_url}"
        parse_mode = telegram.constants.ParseMode.HTML

        # Upload to Telegram with error handling
        try:
            with open(audio_filename, "rb") as audio_file:
                await bot.send_audio(
                    chat_id=TELEGRAM_CHANNEL_ID,
                    audio=audio_file,
                    caption=caption,
                    parse_mode=parse_mode,
                    title=clean_title_[:64],  # Telegram limit
                    performer=uploader[:64],
                    duration=duration if duration else 0,
                    write_timeout=120.0,
                    read_timeout=120.0,
                    connect_timeout=120.0
                )
            logger.info("Audio uploaded successfully to Telegram!")
        except telegram.error.NetworkError as e:
            logger.error(f"Network error during Telegram upload: {e}")
            sys.exit(1)
        except telegram.error.BadRequest as e:
            logger.error(f"Bad request error during Telegram upload: {e}")
            sys.exit(1)
        except telegram.error.TelegramError as e:
            logger.error(f"Telegram API error: {e}")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)
    finally:
        # Cleanup temporary directory
        if temp_dir and os.path.exists(temp_dir):
            retries = 3
            for attempt in range(retries):
                try:
                    shutil.rmtree(temp_dir)
                    logger.info(f"Cleaned up temporary directory: {temp_dir}")
                    break
                except PermissionError as e:
                    if attempt < retries - 1:
                        logger.error(f"Cleanup attempt {attempt + 1} failed. Retrying in 1 second...")
                        time.sleep(1)
                    else:
                        logger.error(f"Failed to clean up temporary directory after {retries} attempts: {e}")

if __name__ == "__main__":
    asyncio.run(main())
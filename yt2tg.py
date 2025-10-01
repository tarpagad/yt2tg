#coding: utf-8
import yt_dlp
import os
import sys
import asyncio
import telegram
from datetime import datetime
import re
import tempfile
import shutil
import time
import urllib.parse
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
DEFAULT_MAX_ABR = 192  # kbps

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

async def main():
    """
    Downloads audio from a YouTube video, extracts it as MP3, adds metadata, and uploads it to Telegram.
    """
    if len(sys.argv) < 2:
        print("Usage: python youtube_telegram_uploader.py <youtube_video_url>")
        sys.exit(1)

    # Extract video ID from URL
    parsed_url = urllib.parse.urlparse(sys.argv[1])
    query_params = urllib.parse.parse_qs(parsed_url.query)
    video_id = None

    # Handle standard YouTube URLs (e.g., https://www.youtube.com/watch?v=dQw4w9WgXcQ)
    if 'v' in query_params:
        video_id = query_params['v'][0]
    # Handle short YouTube URLs (e.g., https://youtu.be/dQw4w9WgXcQ)
    elif parsed_url.netloc == 'youtu.be':
        video_id = parsed_url.path.lstrip('/')
    
    if not video_id:
        logging.error("Error: Could not extract video ID from URL")
        sys.exit(1)
    
    video_url = video_id  # Use video ID directly for yt_dlp

    temp_dir = None
    audio_filename = None
    thumbnail_filename = None

    try:
        # Validate Telegram bot token
        if not TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")

        # Create a temporary directory for downloads
        temp_dir = tempfile.mkdtemp()

        # Enhanced ydl options
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio',  # Prefer m4a format if available
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',  # Extract audio using FFmpeg
                'preferredcodec': 'mp3',      # Convert to MP3 format
                'preferredquality': str(DEFAULT_MAX_ABR),  # Set bitrate
            }],
            'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),  # Use absolute path
            'writethumbnail': True,         # Write thumbnail image
            'writeinfojson': True,          # Write metadata JSON
            'quiet': False,                 # Disable quiet mode for debugging
            'no_warnings': False,           # Show warnings
            'extract_flat': False,          # Full extract for single video
            'verbose': os.getenv("VERBOSE", "False").lower() == "true",  # Configurable verbosity
        }

        # Extract info first to get title, uploader, duration, etc.
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info_dict = ydl.extract_info(video_url, download=False)
            except yt_dlp.utils.DownloadError as e:
                logger.error(f"Error extracting video info: {e}")
                sys.exit(1)

            title = info_dict.get('title', 'Unknown Title')
            uploader = info_dict.get('uploader', 'Unknown')
            duration = info_dict.get('duration', 0)
            upload_date = info_dict.get('upload_date')
            thumbnail = info_dict.get('thumbnail')  # Get thumbnail URL from info_dict

            # Parse upload date
            date = None
            if upload_date:
                try:
                    date = datetime.strptime(upload_date, '%Y%m%d')
                except ValueError:
                    pass

            # Clean title
            clean_title_ = clean_title(title)

            # Format filename
            ext = '.mp3'
            formatted_filename = os.path.join(temp_dir, f"{clean_title_}{ext}")

            # Download the video/audio
            try:
                ydl.download([video_url])
            except yt_dlp.utils.DownloadError as e:
                logger.error(f"Download failed: {e}")
                sys.exit(1)

            # Find the downloaded audio file
            audio_files = [f for f in os.listdir(temp_dir) if f.endswith('.mp3')]
            if audio_files:
                audio_filename = os.path.join(temp_dir, audio_files[0])  # Use first MP3 file
                # Rename to formatted if different
                if audio_filename != formatted_filename:
                    os.rename(audio_filename, formatted_filename)
                    audio_filename = formatted_filename
            else:
                raise Exception("No audio file downloaded")

            # Find thumbnail using info_dict or file search
            if thumbnail:
                thumbnail_extensions = ['.jpg', '.webp', '.png', '.jpeg']
                for ext in thumbnail_extensions:
                    potential_thumbnail = os.path.join(temp_dir, f"{clean_title_}{ext}")
                    if os.path.exists(potential_thumbnail):
                        thumbnail_filename = potential_thumbnail
                        break

        logger.info(f"Audio downloaded successfully: {audio_filename}")

        # --- Upload to Telegram ---
        logger.info("Uploading to Telegram...")
        bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

        # Prepare caption with original URL
        caption = f"<strong>{title}</strong>\n\n<b>Vidéo source:</b> {sys.argv[1]}"
        parse_mode = telegram.constants.ParseMode.HTML

        # Upload to Telegram with error handling
        try:
            with open(audio_filename, "rb") as audio_file:
                if thumbnail_filename and os.path.exists(thumbnail_filename):
                    with open(thumbnail_filename, "rb") as thumb_file:
                        await bot.send_audio(
                            chat_id=TELEGRAM_CHANNEL_ID,
                            audio=audio_file,
                            caption=caption,
                            parse_mode=parse_mode,
                            title=clean_title_[:64],  # Telegram limit
                            performer=uploader[:64],
                            duration=duration,
                            write_timeout=120.0,
                            read_timeout=120.0,
                            connect_timeout=120.0,
                            thumbnail=thumb_file
                        )
                else:
                    await bot.send_audio(
                        chat_id=TELEGRAM_CHANNEL_ID,
                        audio=audio_file,
                        caption=caption,
                        parse_mode=parse_mode,
                        title=clean_title_[:64],
                        performer=uploader[:64],
                        duration=duration,
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

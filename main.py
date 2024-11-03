import os
import subprocess
import re
import feedparser
import asyncio
import logging
from pyrogram import Client
from config import *
from database import connect_to_mongodb, insert_document
from datetime import datetime
from tor2mag import *
import random
import string
from torrentp import TorrentDownloader


# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize connections
db = connect_to_mongodb(MONGODB_URI, "Spidydb")
collection_name = "Prips"

# Pyrogram client initialization
app = Client(
    name="PRips-bot",
    api_hash=API_HASH,
    api_id=int(API_ID),
    bot_token=BOT_TOKEN,
    workers=300
)



async def download_torrent(magnet_link,file_path):
    torrent_file = TorrentDownloader(magnet_link, file_path)
    await torrent_file.start_download()


def generate_random_string(length):
    characters = string.ascii_letters + string.digits + string.punctuation
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string

def convert_pixhost_link(original_url):
    parts = original_url.split('/')
    if len(parts) > 5:
        number = parts[4]
        image_id = parts[5].split('_')[0]
        return f"https://t0.pixhost.to/thumbs/{number}/{image_id}_cover.jpg"
    return "Invalid Pixhost link"

def fetch_rss_links(rss_url):
    feed = feedparser.parse(rss_url)
    if feed.bozo:
        logging.error("Error fetching the RSS feed.")
        return []

    entries_info = []
    for entry in feed.entries:
        title = entry.title
        content = entry.content[0].value

        try:
            release = re.search(r'<strong>Release:</strong>\s*(.*?)<br', content).group(1).strip()
            file_size = re.search(r'<strong>File Size:</strong>\s*(.*?)<br', content).group(1).strip()
            duration = re.search(r'<strong>Duration:</strong>\s*(.*?)</p>', content).group(1).strip()
            torrent_link = re.search(r'href="(https://[^"]*\.torrent)"', content).group(1)

            pixhost_link_match = re.search(r'(https://pixhost\.to/show/\d+/\d+_cover\.jpg)', content)
            pixhost_link = convert_pixhost_link(pixhost_link_match.group(1)) if pixhost_link_match else "No Pixhost link found"

            entries_info.append((title, file_size, duration, torrent_link, pixhost_link))
        except AttributeError as e:
            logging.warning(f"Missing information in feed entry: {title}. Error: {e}")

    return entries_info

def generate_thumbnail(file_name, output_filename):
    command = [
        'vcsi', file_name, '-t', '-g', '2x2',
        '--metadata-position', 'hidden',
        '--start-delay-percent', '35', '-o', output_filename
    ]
    try:
        subprocess.run(command, check=True, capture_output=True)
        logging.info(f"Thumbnail saved as {output_filename}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error generating thumbnail for {file_name}: {e}")

async def start_download():
    async with app:
        rss_url = "https://pornrips.to/feed/"
        results = fetch_rss_links(rss_url)
        logging.info(f"Total links found: {len(results)}")

        for title, file_size, duration, torrent_link, pixhost_link in results:
            magnet_link = convert_torrent_url_to_magnet(torrent_link)
            logging.info(f"Starting download: {title} from {magnet_link}")
            try:
                gid = generate_random_string(10)
                download_path = f"Downloads/{gid}"
                os.makedirs(download_path, exist_ok=True)
                
                await download_torrent(magnet_link, download_path)

                video_files = [f for f in os.listdir(download_path) if f.endswith(('.mp4', '.mkv'))]
                if not video_files:
                    logging.warning(f"No video files found in {download_path}.")
                    continue

                file_path = os.path.join(download_path, video_files[0])
                thumb_path = f"{download_path}/{title}.png"
                generate_thumbnail(file_path, thumb_path)

                video_message = await app.send_video(
                    DUMP_ID, video=file_path, thumb=thumb_path, caption=title
                )
                result = {
                    "ID": video_message.id,
                    "File_Name": title,
                    "Video_Link": torrent_link,
                }
                insert_document(db, collection_name, result)

                os.remove(file_path)
                os.remove(thumb_path)
                os.rmdir(download_path)

            except Exception as e:
                logging.error(f"Error during download process for {title}: {e}")

if __name__ == "__main__":
    app.run(start_download())

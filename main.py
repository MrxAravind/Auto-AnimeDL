import os
import subprocess
import re
import feedparser
import asyncio
from pyrogram import Client
from config import *
from database import connect_to_mongodb, insert_document
from downloader import connect_aria2, add_download,list_downloads
from datetime import datetime
import time
from tor2mag import *

# Initialize connections
api = connect_aria2()
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

def convert_pixhost_link(original_url):
    parts = original_url.split('/')
    number = parts[4]
    image_id = parts[5].split('_')[0]
    return f"https://t0.pixhost.to/thumbs/{number}/{image_id}_cover.jpg"

def fetch_rss_links(rss_url):
    feed = feedparser.parse(rss_url)
    if feed.bozo:
        print("Error fetching the RSS feed.")
        return []

    entries_info = []
    for entry in feed.entries:
        title = entry.title
        content = entry.content[0].value

        release = re.search(r'<strong>Release:</strong>\s*(.*?)<br', content).group(1).strip()
        file_size = re.search(r'<strong>File Size:</strong>\s*(.*?)<br', content).group(1).strip()
        duration = re.search(r'<strong>Duration:</strong>\s*(.*?)</p>', content).group(1).strip()
        torrent_link = re.search(r'href="(https://[^"]*\.torrent)"', content).group(1)

        pixhost_link_match = re.search(r'(https://pixhost\.to/show/\d+/\d+_cover\.jpg)', content)
        pixhost_link = convert_pixhost_link(pixhost_link_match.group(1)) if pixhost_link_match else "No Pixhost link found"

        entries_info.append((title, file_size, duration, torrent_link, pixhost_link))

    return entries_info

def generate_thumbnail(file_name, output_filename):
    command = [
        'vcsi', file_name, '-t', '-g', '2x2',
        '--metadata-position', 'hidden',
        '--start-delay-percent', '35', '-o', output_filename
    ]
    try:
        subprocess.run(command, check=True, capture_output=True)
        print(f"Thumbnail saved as {output_filename}")
    except subprocess.CalledProcessError as e:
        print(f"Error generating thumbnail for {file_name}: {e}")

async def start_download():
    async with app:
        rss_url = "https://pornrips.to/feed/"
        results = fetch_rss_links(rss_url)
        print(f"Total links found: {len(results)}")

        for title, file_size, duration, torrent_link, pixhost_link in results:
            magnet_link = convert_torrent_url_to_magnet(torrent_link)
            print(f"Starting download: {title} from {magnet_link}") 
            try:
                file_path = f"{title}.mp4"
                download = add_download(api, magnet_link, file_path)
                start_time = datetime.now()
                if not download:
                    print(f"Failed to add download for {title}")
                    continue
                while not download.is_complete:
                    download.update()
                    list_downloads(api,start_time)
                    time.sleep(4)
                    
                    
                # Get the file path from the completed download
                thumb_path = f"Downloads/{title}.png"
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

                # Cleanup
                os.remove(file_path)
                os.remove(thumb_path)

            except Exception as e:
                print(f"Error during download process for {title}: {e}")

if __name__ == "__main__":
    app.run(start_download())

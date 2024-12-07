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
import random
import string
from seedrcc import Login,Seedr
from download import *



# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# Suppress Pyrogram logging
logging.getLogger("pyrogram").setLevel(logging.WARNING)  # Change this to ERROR or CRITICAL if you want less output


# Initialize connections
db = connect_to_mongodb(MONGODB_URI, "Spidydb")
collection_name = "AutoAnime"

seedr = Login('mrhoster07@gmail.com', 'hatelenovo@33')

response = seedr.authorize()
account = Seedr(token=seedr.token)


downloader = Aria2cDownloader(max_concurrent_downloads=5)


# Pyrogram client initialization
app = Client(
    name="Anime-bot",
    api_hash=API_HASH,
    api_id=int(API_ID),
    bot_token=BOT_TOKEN,
    workers=300
)


def add_dl(file_name,url):
    downloader.download_file(url,filename=file_name,
       download_options={
        'max-download-limit': '500K',
        'checksum': 'sha-256=abc123...'
         })
    downloader.start_downloads()
    return downloader.get_download_results()

def generate_random_string(length):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))

def convert_pixhost_link(original_url):
    parts = original_url.split('/')
    if len(parts) > 5:
        number = parts[4]
        image_id = parts[5].split('_')[0]
        return f"https://t0.pixhost.to/thumbs/{number}/{image_id}_cover.jpg"
    return "Invalid Pixhost link"


def rename_files(filename):
    pattern = r"\[.*?\]"
    if "[SubsPlease]" in filename:
            new_name = re.sub(pattern, "", filename).strip()     
            title = os.path.basename(new_name)
            old_file_path = filename
            new_file_path = new_name
            os.rename(old_file_path, new_file_path)
            print(f"Renamed: {filename} -> {new_name}")
            return title,new_file_path

    
def check_for_video_files(download_path):
    video_files = []
    for root, _, files in os.walk(download_path):
        for f in files:
            if f.endswith(('.mp4', '.mkv')):
                video_files.append(os.path.join(root, f))

    if not video_files:
        logging.warning(f"No video files found in {download_path}.")
        return video_files  # Return an empty list
    else:
        logging.info(f"Found video files: {video_files}")
        return video_files  # Return list of found files

def fetch_rss_links(rss_url):
    feed = feedparser.parse(rss_url)
    if feed.bozo:
        logging.error("Error fetching the RSS feed.")
        return []

    entries_info = []
    for entry in feed.entries:
        title = entry.title
        try:
            magnet_link = entry.link

            entries_info.append((title,magnet_link))
        except AttributeError as e:
            logging.warning(f"Missing information in feed entry: {title}. Error: {e}")

    return entries_info


def seedr(title,torrent):
  try:
     account.addTorrent('magnet:?xt=urn:btih:LQUJ4PBRIP4TXPZJOILHGL3EJR77DYBG&dn=%5BSubsPlease%5D%20Dandadan%20-%2010%20%281080p%29%20%5BDE4B4411%5D.mkv&xl=1446930174&tr=http%3A%2F%2Fnyaa.tracker.wf%3A7777%2Fannounce&tr=udp%3A%2F%2Ftracker.coppersurfer.tk%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337%2Fannounce&tr=udp%3A%2F%2F9.rarbg.to%3A2710%2Fannounce&tr=udp%3A%2F%2F9.rarbg.me%3A2710%2Fannounce&tr=udp%3A%2F%2Ftracker.leechers-paradise.org%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker.internetwarriors.net%3A1337%2Fannounce&tr=udp%3A%2F%2Ftracker.cyberia.is%3A6969%2Fannounce&tr=udp%3A%2F%2Fexodus.desync.com%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker3.itzmx.com%3A6961%2Fannounce&tr=udp%3A%2F%2Ftracker.torrent.eu.org%3A451%2Fannounce&tr=udp%3A%2F%2Ftracker.tiny-vps.com%3A6969%2Fannounce&tr=udp%3A%2F%2Fretracker.lanta-net.ru%3A2710%2Fannounce&tr=http%3A%2F%2Fopen.acgnxtracker.com%3A80%2Fannounce&tr=wss%3A%2F%2Ftracker.openwebtorrent.com')
     response = account.listContents()
     folder_id = response["folders"][0]["id"]
     response = account.listContents(folder_id)
     file_id = response["files"][0]['folder_file_id']
     response = account.fetchFile(file_id)
     return response["name"],response["url"]
  except:
      logging.error(f"Error generating Seedr Link for {title}")


def generate_thumbnail(file_name, output_filename):
    command = [
        'vcsi', file_name, '-t', '-g', '1x1',
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
        rss_url = "https://subsplease.org/rss"
        results = fetch_rss_links(rss_url)
        logging.info(f"Total links found: {len(results)}")

        for title,magnet_link in results:
            logging.info(f"Starting download: {title} from {magnet_link}")
            try:
                gid = generate_random_string(10)
                download_path = f"Downloads/{gid}"
                os.makedirs(download_path, exist_ok=True)
                name,direct_link = seedr(title,torrent)
                add_dl(name,direct_link)
                video_files = check_for_video_files(download_path)
                if not video_files:
                    logging.warning(f"No video files found in {download_path}.")
                    continue
                file_path = video_files[0]
                title,new_file_path = rename_files(file_path)
                thumb_path = os.path.join(download_path, f"{title}.png")
                generate_thumbnail(new_file_path, thumb_path)

                video_message = await app.send_document(
                    DUMP_ID, document=new_file_path, thumb=thumb_path, caption=name
                )
                result = {
                    "ID": video_message.id,
                    "File_Name": title,
                    "Video_Link": torrent_link,
                }
                insert_document(db, collection_name, result)

                os.remove(new_file_path)
                os.remove(thumb_path)
                os.rmdir(download_path)
            except Exception as e:
                logging.error(f"Error during download process for {title} : {e}")

if __name__ == "__main__":
    app.run(start_download())

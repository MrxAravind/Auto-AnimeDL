import os
import asyncio
import logging
from pyrogram import Client
from config import *
from database import connect_to_mongodb, insert_document
from datetime import datetime
from seedr import *
from download import *
from tools import *



# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# Suppress Pyrogram logging
logging.getLogger("pyrogram").setLevel(logging.WARNING)  # Change this to ERROR or CRITICAL if you want less output


# Initialize connections
db = connect_to_mongodb(MONGODB_URI, "Spidydb")
collection_name = "AutoAnime"



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
    res = downloader.download_file(url,filename=file_name,)
    res = downloader.start_downloads()
    return downloader.get_download_results()


async def start_download():
    async with app:
        try: 
                rss_url = "https://subsplease.org/rss/"
                results = fetch_rss_links(rss_url)
                download_path = f"downloads"
                logging.info(f"Total links found: {len(results)}")
                clean_downloads()
                
                   
                for title,magnet_link in results[8:]:
                        delete_files()
                        logging.info(f"Starting download: {magnet_link}")            
                        
                        os.makedirs(download_path, exist_ok=True)
                        
                        response = add_mag(title,magnet_link)
                        time.sleep(10)

                        data = list_files()
                        for folderId,fileId,name in data:
                            if name == title and response["title"] == name and title ==  response["title"]:
                               f,link = gen_link(fileId)

                        res = add_dl(name,link)


                        video_files = check_for_video_files(download_path)
                        if not video_files:
                            logging.warning(f"No video files found in {download_path}.")
                            continue

                        file_path = video_files[0]
        
                        if "[SubsPlease]" in file_path:
                            title = re.sub(r"\[.*?\]", "", title).strip() 
                        
                        thumb_path = os.path.join(download_path, f"{title}.png")
                        generate_thumbnail(file_path, thumb_path)
                        t,file_path =  rename_files(file_path)

                        video_message = await app.send_document(
                            DUMP_ID, document=file_path, thumb=thumb_path, caption=title
                        )
                        result = {
                            "ID": video_message.id,
                            "File_Name": title,
                            "Video_Link":magnet_link,
                        }
                        insert_document(db, collection_name, result)
                        clean_downloads()

                        
        
        except Exception as e:
                logging.error(f"Error during download process for : {e}")

if __name__ == "__main__":
     app.run(start_download())

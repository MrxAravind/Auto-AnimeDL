import subprocess
import logging
import feedparser
import os
import re
import string
import random
import shutil



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


def clean_downloads():
    download_path = 'downloads'
    for filename in os.listdir(download_path):
                file_path = os.path.join(download_path, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
    os.rmdir(download_path)



def convert_pixhost_link(original_url):
    parts = original_url.split('/')
    if len(parts) > 5:
        number = parts[4]
        image_id = parts[5].split('_')[0]
        return f"https://t0.pixhost.to/thumbs/{number}/{image_id}_cover.jpg"
    return "Invalid Pixhost link"



def generate_random_string(length):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))
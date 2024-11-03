import requests
import bencodepy
import hashlib
import os

def download_torrent(torrent_url, save_path):
    response = requests.get(torrent_url)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(response.content)
        return save_path
    else:
        raise Exception(f"Failed to download torrent file: {response.status_code}")

def torrent_to_magnet(torrent_file_path):
    with open(torrent_file_path, 'rb') as f:
        torrent_data = bencodepy.decode(f.read())
    
    info = torrent_data[b'info']
    info_hash = hashlib.sha1(bencodepy.encode(info)).hexdigest()
    name = info[b'name'].decode('utf-8')
    
    magnet_link = f"magnet:?xt=urn:btih:{info_hash}&dn={name}"
    return magnet_link

def convert_torrent_url_to_magnet(torrent_url):
    # Download the torrent file
    torrent_file_path = 'temp.torrent'  # Temporary file to store the downloaded torrent
    download_torrent(torrent_url, torrent_file_path)
    
    # Convert to magnet link
    magnet_link = torrent_to_magnet(torrent_file_path)
    
    # Optionally, remove the temporary torrent file
    os.remove(torrent_file_path)
    
    return magnet_link


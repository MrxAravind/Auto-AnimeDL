import qbittorrent
import os
from tabulate import tabulate

# Connect to qBittorrent daemon
def connect_qbittorrent():
    qb = qbittorrent.Client()
    qb.login('your_username', 'your_password')  # Replace with your qBittorrent credentials
    return qb

# Add a download with a specified filename
def add_download(qb, url, filename):
    try:
        qb.download_from_link(url, savepath='', name=filename)
        print(f"Download added with filename: {filename}")
    except Exception as e:
        print(f"Failed to add download: {e}")

# Pause a download by torrent hash
def pause_download(qb, torrent_hash):
    try:
        qb.pause(torrent_hash)
        print(f"Download paused: {torrent_hash}")
    except Exception as e:
        print(f"Failed to pause download: {e}")

# Resume a download by torrent hash
def resume_download(qb, torrent_hash):
    try:
        qb.resume(torrent_hash)
        print(f"Download resumed: {torrent_hash}")
    except Exception as e:
        print(f"Failed to resume download: {e}")

# Remove a download by torrent hash
def remove_download(qb, torrent_hash):
    try:
        qb.delete(torrent_hash)
        print(f"Download removed: {torrent_hash}")
    except Exception as e:
        print(f"Failed to remove download: {e}")

# Get the status of all downloads
def get_downloads_status(qb):
    try:
        torrents = qb.torrents()
        for torrent in torrents:
            print(f"Hash: {torrent['hash']}, Status: {torrent['state']}, Progress: {torrent['progress'] * 100:.1f}%")
    except Exception as e:
        print(f"Failed to retrieve downloads status: {e}")

# Purge completed/removed downloads (not applicable in qBittorrent API, but can be managed via removal)
def purge_downloads(qb):
    print("Use remove_download() to manage completed/removed torrents.")

# List all downloads with detailed information
def list_downloads(qb):
    try:
        # Clear the screen
        os.system('cls' if os.name == 'nt' else 'clear')

        torrents = qb.torrents()
        if not torrents:
            print("No downloads found")
            return

        download_info = []
        for torrent in torrents:
            # Prepare row data
            row = [
                torrent['hash'][:8],  # Truncated hash for readability
                torrent['name'][:30] + '...' if len(torrent['name']) > 30 else torrent['name'],  # Truncated filename
                torrent['state'],
                f"{torrent['progress'] * 100:.1f}%",
                f"{torrent['size'] / 1024 / 1024:.1f} MB",  # Size in MB
                f"{torrent['download_speed'] / 1024 / 1024:.2f} MB/s",  # Speed in MB/s
                torrent['added_on'],  # Added timestamp (may need formatting)
                torrent['status']  # Any error message or status info
            ]
            download_info.append(row)

        # Print table using tabulate
        headers = ["Hash", "Name", "Status", "Progress", "Size", "Speed", "Added On", "Error"]
        print(tabulate(download_info, headers=headers, tablefmt="grid"))

    except Exception as e:
        print(f"Failed to list downloads: {e}")

# Example usage
if __name__ == "__main__":
    qb = connect_qbittorrent()
    # Add your desired functionality here, e.g., adding a download, listing, etc.

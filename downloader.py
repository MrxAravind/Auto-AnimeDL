import aria2p
from datetime import datetime
from tabulate import tabulate

# Connect to aria2c daemon
def connect_aria2():
    return aria2p.API(
        aria2p.Client(
            host="http://localhost",  # Change this if your aria2c daemon is hosted elsewhere
            port=6800,
            secret=""  # If you have an RPC secret, add it here
        )
    )

# Add a download with a specified filename
def add_download(api, url, filename):
    try:
        # Set the options for the download
        options = {"out": filename}  # Specify the desired filename
        download_list = api.add(url, options=options)

        # Collect the gids
        gids = []

        if isinstance(download_list, list):
            for download in download_list:
                print(f"Download added: {download.gid} with filename: {filename}")
                gids.append(download)
        else:
            download = download_list
            print(f"Download added: {download.gid} with filename: {filename}")
            gids.append(download)

        return gids[0]
    except Exception as e:
        print(f"Failed to add download: {e}")
        return None

# Pause a download by GID
def pause_download(api, gid):
    try:
        api.pause(gid)
        print(f"Download paused: {gid}")
    except Exception as e:
        print(f"Failed to pause download: {e}")

# Resume a download by GID
def resume_download(api, gid):
    try:
        api.resume(gid)
        print(f"Download resumed: {gid}")
    except Exception as e:
        print(f"Failed to resume download: {e}")

# Remove a download by GID
def remove_download(api, gid):
    try:
        api.remove([gid], force=True)
        print(f"Download removed: {gid}")
    except Exception as e:
        print(f"Failed to remove download: {e}")

# Get the status of all downloads
def get_downloads_status(api):
    try:
        downloads = api.get_downloads()
        for download in downloads:
            print(f"GID: {download.gid}, Status: {download.status}, Progress: {download.progress_string()}")
    except Exception as e:
        print(f"Failed to retrieve downloads status: {e}")

# Purge completed/removed downloads
def purge_downloads(api):
    try:
        api.purge()
        print("Purged completed/removed downloads")
    except Exception as e:
        print(f"Failed to purge downloads: {e}")

# List all downloads with detailed information
def list_downloads(api,start_time):
    try:
        downloads = api.get_downloads()
        if not downloads:
            print("No downloads found")
            return

        download_info = []
        for download in downloads:
            # Calculate download speed in MB/s
            speed_mb = download.download_speed / 1024 / 1024
            
            # Calculate size in MB
            total_mb = download.total_length / 1024 / 1024
            completed_mb = download.completed_length / 1024 / 1024

            # Format timestamp
            timestamp = start_time

            # Prepare row data
            row = [
                download.gid[:8],  # Truncated GID for readability
                download.name[:30] + '...' if len(download.name) > 30 else download.name,  # Truncated filename
                download.status,
                f"{download.progress:.1f}%",
                f"{completed_mb:.1f}/{total_mb:.1f} MB",
                f"{speed_mb:.2f} MB/s",
                timestamp,
                download.error_message[:30] if download.error_message else ''
            ]
            download_info.append(row)

        # Print table using tabulate
        headers = ["GID", "Name", "Status", "Progress", "Size", "Speed", "Start Time", "Error"]
        print(tabulate(download_info, headers=headers, tablefmt="grid"))

    except Exception as e:
        print(f"Failed to list downloads: {e}")

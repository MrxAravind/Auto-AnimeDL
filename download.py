import subprocess
import os
import threading
import queue
import time
import json
import argparse
from typing import List, Dict, Optional, Callable

class Aria2cDownloader:
    def __init__(self, 
                 max_concurrent_downloads: int = 5, 
                 download_dir: str = './Downloads', 
                 aria2c_path: str = 'aria2c'):
        """
        Initialize the Aria2c Downloader
        
        Args:
            max_concurrent_downloads (int): Maximum number of concurrent downloads
            download_dir (str): Directory to save downloaded files
            aria2c_path (str): Path to aria2c executable
        """
        self.max_concurrent_downloads = max_concurrent_downloads
        self.download_dir = os.path.abspath(download_dir)
        self.aria2c_path = aria2c_path
        
        # Ensure download directory exists
        os.makedirs(self.download_dir, exist_ok=True)
        
        # Download queue and tracking
        self.download_queue = queue.Queue()
        self.active_downloads = {}
        self.download_results = {}
        
        # Create a lock for thread-safe operations
        self.lock = threading.Lock()

    def download_file(self, 
                      url: str, 
                      filename: Optional[str] = None, 
                      download_options: Optional[Dict[str, str]] = None) -> Dict:
        """
        Add a file to the download queue
        
        Args:
            url (str): URL of the file to download
            filename (str, optional): Custom filename for the download
            download_options (dict, optional): Additional aria2c options
        
        Returns:
            dict: Download configuration
        """
        options = download_options or {}
        
        # Generate unique download ID
        download_id = f"download_{int(time.time())}_{hash(url)}"
        
        # Prepare download configuration
        download_config = {
            'id': download_id,
            'url': url,
            'filename': filename or os.path.basename(url),
            'options': options,
            'status': 'queued'
        }
        
        self.download_queue.put(download_config)
        return download_config

    def _run_download(self, download_config: Dict):
        """
        Execute a single download using aria2c
        
        Args:
            download_config (dict): Download configuration
        """
        url = download_config['url']
        download_id = download_config['id']
        filename = download_config.get('filename')
        options = download_config.get('options', {})
        
        # Prepare aria2c command
        cmd = [
            self.aria2c_path,
            '-d', self.download_dir,
            '-o', filename,
            '--console-log-level=notice',
            '--summary-interval=5',
            '--download-result=full',
            '--max-connection-per-server=5',
            '--split=5',
            '--max-concurrent-downloads=5'
        ]
        
        # Add custom options
        for key, value in options.items():
            cmd.append(f'--{key}={value}')
        
        cmd.append(url)
        
        try:
            # Run download and capture output
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=3600  # 1-hour timeout
            )
            
            # Update download results
            with self.lock:
                self.download_results[download_id] = {
                    'status': 'completed' if result.returncode == 0 else 'failed',
                    'returncode': result.returncode,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'filepath': os.path.join(self.download_dir, filename) if filename else None
                }
        
        except subprocess.TimeoutExpired:
            with self.lock:
                self.download_results[download_id] = {
                    'status': 'timeout',
                    'filepath': None
                }
        
        except Exception as e:
            with self.lock:
                self.download_results[download_id] = {
                    'status': 'error',
                    'error': str(e),
                    'filepath': None
                }
        
        finally:
            # Remove from active downloads
            with self.lock:
                if download_id in self.active_downloads:
                    del self.active_downloads[download_id]

    def start_downloads(self):
        """
        Start processing download queue with concurrent downloads
        """
        download_threads = []
        
        while not self.download_queue.empty():
            # Check if we've reached max concurrent downloads
            if len(download_threads) >= self.max_concurrent_downloads:
                # Remove completed threads
                download_threads = [t for t in download_threads if t.is_alive()]
                time.sleep(1)
                continue
            
            # Get next download from queue
            download_config = self.download_queue.get()
            download_id = download_config['id']
            
            # Create and start download thread
            thread = threading.Thread(
                target=self._run_download, 
                args=(download_config,)
            )
            thread.start()
            
            # Track active downloads
            with self.lock:
                self.active_downloads[download_id] = thread
            
            download_threads.append(thread)
        
        # Wait for all downloads to complete
        for thread in download_threads:
            thread.join()

    def get_download_results(self) -> Dict:
        """
        Retrieve download results
        
        Returns:
            dict: Dictionary of download results
        """
        return dict(self.download_results)

def main():
    """
    Main function to demonstrate usage of Aria2c Downloader
    """
    parser = argparse.ArgumentParser(description='Advanced Aria2c Downloader')
    parser.add_argument('urls', nargs='+', help='URLs to download')
    parser.add_argument('--max-downloads', type=int, default=5, 
                        help='Maximum concurrent downloads')
    parser.add_argument('--download-dir', default='./downloads', 
                        help='Directory to save downloads')
    
    args = parser.parse_args()
    
    # Create downloader instance
    downloader = Aria2cDownloader(
        max_concurrent_downloads=args.max_downloads,
        download_dir=args.download_dir
    )
    
    # Add URLs to download queue
    for url in args.urls:
        downloader.download_file(url)
    
    # Start downloads
    downloader.start_downloads()
    
    # Print download results
    results = downloader.get_download_results()
    print(json.dumps(results, indent=2))

if __name__ == '__main__':
    main()

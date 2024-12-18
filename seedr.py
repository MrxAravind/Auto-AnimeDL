from seedrcc import Login,Seedr
import logging
import time

logging.basicConfig(filename='seedr.log', level=logging.INFO)

seedr = Login('mrhoster07@gmail.com', 'hatelenovo@22')
response = seedr.authorize()
account = Seedr(token=seedr.token)

def add_mag(title, torrent):
    try:
        response = account.addTorrent(torrent)
        time.sleep(10)
        logging.info(f"Added torrent for {title}")
        return response
    except Exception as e:
        logging.error(f"Error Adding Torret for {title} : {e}")

def delete_files():
    try:
        response = account.listContents()
        folder_ids = [folder["id"] for folder in response["folders"]]
        for folder_id in folder_ids:
            folder_contents = account.listContents(folder_id)
            for file in folder_contents["files"]:
                file_id = file['folder_file_id']
                file_name = file['name']
                account.deleteFile(fileId=file_id)
                logging.info(f"Deleted file: {file_name} (ID: {file_id})")
            account.deleteFolder(folderId=folder_id)
            logging.info(f"Deleted folder with ID: {folder_id}")
    except:
        logging.error("Error deleting files and folders")


def list_files():
    try:
        data = []
        response = account.listContents()
        folder_ids = [folder["id"] for folder in response["folders"]]
        for folder_id in folder_ids:
            folder_contents = account.listContents(folder_id)
            for file in folder_contents["files"]:
                file_id = file['folder_file_id']
                title = file['name']
                if title.endswith((".mkv", ".mp4")):
                    data.append([folder_id, file_id, title])
                    logging.info(f"Found file: {title}")
        print(data)
    except:
        logging.error("Error generating Seedr File Search")

def gen_link(file_id):
    try:
        response = account.fetchFile(file_id)
        if response:
            logging.info(f"Generated link for file with ID: {file_id}")
            return response["name"], response["url"]
    except:
        logging.error(f"Error generating link for file with ID: {file_id}")


delete_files()
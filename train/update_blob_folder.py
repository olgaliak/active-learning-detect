import os
from pathlib import Path
def update_folder(folder_name, block_blob_service, container_name):
    existing_files = {os.path.relpath(os.path.join(directory, cur_file), folder_name) for (directory, _, filenames) 
        in os.walk(folder_name) for cur_file in filenames}
    folder_name = Path(folder_name)
    for blob in block_blob_service.list_blobs(container_name):
        if blob.name not in existing_files:
            (folder_name/blob.name).parent.mkdir(parents=True, exist_ok=True) 
            block_blob_service.get_blob_to_path(container_name, blob.name, str(folder_name/blob.name))
            # TODO: Append onto totag

if __name__ == "__main__":      
    from azure.storage.blob import BlockBlobService
    import sys
    sys.path.append("..")
    from utils.config import Config
    config_file = Config.parse_file("config.ini")
    block_blob_service = BlockBlobService(account_name=config_file["AZURE_STORAGE_ACCOUNT"], account_key=config_file["AZURE_STORAGE_KEY"])
    container_name = config_file["image_container_name"]
    image_folder_name =  config_file["image_dir"]
    update_folder(image_folder_name, block_blob_service, container_name)

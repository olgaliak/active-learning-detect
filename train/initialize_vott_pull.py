import csv
import cv2
from pathlib import Path
import time
def extract_data(filename):
    height, width, _ = cv2.imread(str(filename),1).shape
    return filename.name, height, width

def select_jsons(image_directory, user_folders, classes, csv_filename, map_filename):
    with open(map_filename, "w") as map_file:
        for index, name in enumerate(classes, 1):
            map_file.write("item {{\n  id: {}\n  name: '{}'\n}}".format(index, name))

    image_directory = Path(image_directory)
    if user_folders:
        all_images = [(extract_data(filename),filename.parent) for filename in image_directory.glob('**/*') if filename.is_file()]
    else:
        all_images = [extract_data(filename) for filename in image_directory.iterdir()]

    with open(csv_filename, 'w', newline='') as csv_file:
        csv_writer = csv.writer(csv_file)
        if user_folders:
            csv_writer.writerow(["filename","class","xmin","xmax","ymin","ymax","height","width","folder","box_confidence", "image_confidence"])
            for (filename,true_height,true_width),folder in all_images:
                csv_writer.writerow([filename,"NULL",0,0,0,0,true_height,true_width,folder,0,0])
        else:
            csv_writer.writerow(["filename","class","xmin","xmax","ymin","ymax","height","width","box_confidence", "image_confidence"])
            for (filename,true_height,true_width),folder in all_images:
                csv_writer.writerow([filename,"NULL",0,0,0,0,true_height,true_width,folder,0,0])

if __name__ == "__main__":
    from azure.storage.blob import BlockBlobService
    import sys
    import os
    # Allow us to import utils
    config_dir = str(Path.cwd().parent / "utils")
    if config_dir not in sys.path:
        sys.path.append(config_dir)
    from config import Config
    if len(sys.argv)<2:
        raise ValueError("Need to specify config file")
    config_file = Config.parse_file(sys.argv[1])
    block_blob_service = BlockBlobService(account_name=config_file["AZURE_STORAGE_ACCOUNT"], account_key=config_file["AZURE_STORAGE_KEY"])
    container_name = config_file["label_container_name"]
    select_jsons(config_file["image_dir"],config_file["user_folders"]=="True", config_file["classes"].split(","), "totag.csv", config_file["label_map_path"])
    block_blob_service.create_blob_from_path(container_name, "{}_{}.{}".format("totag",int(time.time() * 1000),"csv"), "totag.csv")

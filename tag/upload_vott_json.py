from pathlib import Path
import json
import csv
import time
import cv2
import shutil
import re

def extract_data(filename):
    height, width, _ = cv2.imread(str(filename),1).shape
    return filename.name, height, width

def select_jsons(image_directory, user_folders, file_location):
    if user_folders:
        image_directory = Path(image_directory)
        all_images = []
        all_jsons = []
        for subfolder in image_directory.iterdir():
            if subfolder.is_dir():
                all_images.append([extract_data(filename) for filename in sorted(subfolder.iterdir(), 
                    key=lambda fullname: str(fullname.name).lower())])
                all_jsons.append(str(subfolder)+".json")
    else:
        image_directory = Path(image_directory)
        all_images = [[extract_data(filename) for filename in sorted((image_directory/"Images").iterdir(), 
            key=lambda fullname: str(fullname.name).lower())]]
        all_jsons = [str(image_directory/"Images")+".json"]
 
    for json_file, sorted_images in zip(all_jsons, all_images):

        image_directory = Path(json_file.rsplit(".", 1)[0]).stem
        with open(json_file, "r") as read_file:
            json_file = json.load(read_file)["frames"]

        if (file_location/"tagging.csv").is_file():
            with (file_location/"tagging.csv").open(mode='r') as file:
                reader = csv.reader(file)
                header = next(reader)
                tagging_list = list(reader)
        else:
            tagging_list = []
        file_exists = (file_location/"tagged.csv").is_file()
        tagged = set()
        with (file_location/"tagged.csv").open(mode='a', newline='') as csv_file:
            csv_writer = csv.writer(csv_file)
            if not file_exists:
                if user_folders:
                    csv_writer.writerow(["filename","class","xmin","xmax","ymin","ymax","height","width","folder"])
                else:
                    csv_writer.writerow(["filename","class","xmin","xmax","ymin","ymax","height","width"])
            for index,(filename,true_height,true_width) in enumerate(sorted_images):
                tagged.add(filename)
                if filename in json_file:
                    all_frames = json_file[filename]
                    if all_frames:
                        for cur_frame in all_frames:
                            if cur_frame:
                                vott_width = float(cur_frame["width"])
                                vott_height = float(cur_frame["height"])
                                x1 = float(cur_frame["x1"])/vott_width
                                x2 = float(cur_frame["x2"])/vott_width
                                y1 = float(cur_frame["y1"])/vott_height
                                y2 = float(cur_frame["y2"])/vott_height
                                for tag in cur_frame["tags"]:
                                    if user_folders:
                                        csv_writer.writerow([filename,tag,x1,x2,y1,y2,true_height,true_width,image_directory])
                                    else:
                                        csv_writer.writerow([filename,tag,x1,x2,y1,y2,true_height,true_width])
                    else:
                        if user_folders:
                            csv_writer.writerow([filename,"NULL",0,0,0,0,true_height,true_width,image_directory])
                        else:
                            csv_writer.writerow([filename,"NULL",0,0,0,0,true_height,true_width])
        with (file_location/"tagging.csv").open(mode='w', newline='') as tagging:
            tagging_writer = csv.writer(tagging)
            tagging_writer.writerow(header)
            # Does nothing if tagging_list is empty
            for row in filter(lambda x: x[0] not in tagged, tagging_list):
                tagging_writer.writerow(row)

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
    csv_file_loc = Path(config_file["tagging_location"])
    file_date = [(blob.name, blob.properties.last_modified) for blob in block_blob_service.list_blobs(container_name) if re.match(r'tagged_(.*).csv', blob.name)]
    if file_date:
        block_blob_service.get_blob_to_path(container_name, max(file_date, key=lambda x:x[1])[0], str(csv_file_loc/"tagged.csv"))
    file_date = [(blob.name, blob.properties.last_modified) for blob in block_blob_service.list_blobs(container_name) if re.match(r'tagging_(.*).csv', blob.name)]
    if file_date:
        block_blob_service.get_blob_to_path(container_name, max(file_date, key=lambda x:x[1])[0], str(csv_file_loc/"tagging.csv"))
    #TODO: Ensure this parses folder recursively when given tagging location. Remove the .json part
    select_jsons(config_file["tagging_location"],config_file["user_folders"]=="True",csv_file_loc)
    block_blob_service.create_blob_from_path(container_name, "{}_{}.{}".format("tagged",int(time.time() * 1000),"csv"), str(csv_file_loc/"tagged.csv"))
    block_blob_service.create_blob_from_path(container_name, "{}_{}.{}".format("tagging",int(time.time() * 1000),"csv"), str(csv_file_loc/"tagging.csv"))

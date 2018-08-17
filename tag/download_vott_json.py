import csv
import json
from collections import defaultdict
from heapq import nlargest, nsmallest
from typing import List, Tuple, Dict
from pathlib import Path
import shutil
import random
import colorsys

CONFIDENCE_LOCATION = -1
FILENAME_LOCATION = 0
FOLDER_LOCATION = 8

def make_vott_output(all_predictions, output_location, user_folders, image_loc, blob_credentials = None,
        tag_names: List[str] = ["stamp"], tag_colors: List[str] = "#ed1010"):
    folder_name = Path(all_predictions[0][0][FOLDER_LOCATION]).name
    output_location = str(Path(output_location)/folder_name)
    using_blob_storage = blob_credentials is not None
    if using_blob_storage:
        output_location = Path(output_location)
        blob_service, container_name = blob_credentials
    else:
        image_loc = Path(image_loc)
    Path(output_location).mkdir(parents=True, exist_ok=True)
    if user_folders:
        if using_blob_storage:
            if image_loc == "":
                image_loc = Path(all_predictions[0][0][FOLDER_LOCATION]).name
            else:
                image_loc = image_loc + "/" + Path(all_predictions[0][0][FOLDER_LOCATION]).name
        else:
            image_loc = image_loc/all_predictions[0][0][FOLDER_LOCATION]
    for prediction in all_predictions:
        if using_blob_storage:
            print(image_loc + "/" + prediction[0][FILENAME_LOCATION])
            blob_service.get_blob_to_path(container_name, image_loc + "/" + prediction[0][FILENAME_LOCATION],
                    str(output_location/prediction[0][FILENAME_LOCATION]))
        else:
            shutil.copy(str(image_loc/prediction[0][FILENAME_LOCATION]), output_location)
    all_predictions.sort(key=lambda x: x[0][FILENAME_LOCATION])
    dirjson = {}
    dirjson["frames"] = {}
    for i, predictions in enumerate(all_predictions):
        all_frames = []
        set_predictions = defaultdict(list)
        for prediction in predictions:
            set_predictions[tuple(map(float,prediction[2:8]))].append(prediction[1])
        for j,(coordinates, tags) in enumerate(set_predictions.items(), 1):
            # filename,tag,x1,x2,y1,y2,true_height,true_width,image_directory
            x_1, x_2, y_1, y_2, height, width = coordinates
            if tags!=["NULL"] and (x_1,x_2,y_1,y_2)!=(0,0,0,0):
                curframe = {}
                curframe["x1"] = int(x_1*width)
                curframe["y1"] = int(y_1*height)
                curframe["x2"] = int(x_2*width)
                curframe["y2"] = int(y_2*height)
                curframe["id"] = j
                curframe["width"] = width
                curframe["height"] = height
                curframe["type"] = "Rectangle"
                curframe["tags"] = tags
                curframe["name"] = j
                all_frames.append(curframe)
        dirjson["frames"][i] = all_frames
    dirjson["framerate"] = "1"
    dirjson["inputTags"] = ",".join(tag_names)
    dirjson["suggestiontype"] = "track"
    dirjson["scd"] = False
    dirjson["visitedFrames"] = list(range(len(all_predictions)))
    dirjson["tag_colors"] = tag_colors
    with open(str(output_location)+".json","w") as json_out:
        json.dump(dirjson, json_out)

def get_top_rows(file_location, num_rows, user_folders, pick_max):
    with open(file_location+".csv", 'r') as file:
        reader = csv.reader(file)
        header = next(reader)
        csv_list = list(reader)
    if user_folders:
        all_files = defaultdict(lambda: defaultdict(list))
        for row in csv_list:
            all_files[row[FOLDER_LOCATION]][row[0]].append(row)
        all_lists = []
        if pick_max:
            for folder_name in all_files:
                all_lists.append(nlargest(num_rows, all_files[folder_name].values(), key=lambda x:float(x[0][CONFIDENCE_LOCATION])))
            top_rows = max(all_lists,key=lambda x:sum(float(row[0][CONFIDENCE_LOCATION]) for row in x))
        else:
            for folder_name in all_files:
                all_lists.append(nsmallest(num_rows, all_files[folder_name].values(), key=lambda x:float(x[0][CONFIDENCE_LOCATION])))
            top_rows = min(all_lists,key=lambda x:sum(float(row[0][CONFIDENCE_LOCATION]) for row in x))
    else:
        all_files = defaultdict(list)
        for row in csv_list:
            all_files[row[0]].append(row)
        if pick_max:
            top_rows = nlargest(num_rows, all_files.values(), key=lambda x:float(x[0][CONFIDENCE_LOCATION]))
        else:
            top_rows = nsmallest(num_rows, all_files.values(), key=lambda x:float(x[0][CONFIDENCE_LOCATION]))
    tagging_files = {row[0][0] for row in top_rows}
    file_exists = Path(file_location+"_tagging.csv").is_file()
    with open(file_location+"_new.csv", 'w', newline='') as untagged, open(file_location+"_tagging.csv", 'a', newline='') as tagging:
        untagged_writer, tagging_writer = csv.writer(untagged), csv.writer(tagging)
        untagged_writer.writerow(header)
        if not file_exists:
            tagging_writer.writerow(header)
        for row in csv_list:
            (tagging_writer if row[0] in tagging_files else untagged_writer).writerow(row)
    return top_rows

def create_vott_json(file_location, num_rows, user_folders, pick_max, image_loc, output_location, blob_credentials=None, tag_names = ["stamp"]):
    all_files = get_top_rows(file_location, num_rows, user_folders, pick_max)
    make_vott_output(all_files, output_location, user_folders, image_loc, blob_credentials=blob_credentials, tag_names=tag_names,
    tag_colors=['#%02x%02x%02x' % (int(256*r), int(256*g), int(256*b)) for 
            r,g,b in [colorsys.hls_to_rgb(random.random(),0.8 + random.random()/5.0, 0.75 + random.random()/4.0) for _ in tag_names]])

if __name__ == "__main__":
    #create_vott_json(r"C:\Users\t-yapand\Desktop\GAUCC1_1533070087147.csv",20, True, r"C:\Users\t-yapand\Desktop\GAUCC", r"C:\Users\t-yapand\Desktop\Output\GAUCC")
    import re
    import time
    from azure.storage.blob import BlockBlobService
    import sys
    import os
    # Allow us to import utils
    config_dir = str(Path.cwd().parent / "utils")
    if config_dir not in sys.path:
        sys.path.append(config_dir)
    from config import Config
    if len(sys.argv)<3:
        raise ValueError("Need to specify number of images (first arg) and config file (second arg)")
    config_file = Config.parse_file(sys.argv[2])
    block_blob_service = BlockBlobService(account_name=config_file["AZURE_STORAGE_ACCOUNT"], account_key=config_file["AZURE_STORAGE_KEY"])
    container_name = config_file["label_container_name"]
    file_date = [(blob.name, blob.properties.last_modified) for blob in block_blob_service.list_blobs(container_name) if re.match(r'totag_(.*).csv', blob.name)]
    block_blob_service.get_blob_to_path(container_name, max(file_date, key=lambda x:x[1])[0], "totag.csv")
    container_name = config_file["image_container_name"]
    file_date = [(blob.name, blob.properties.last_modified) for blob in block_blob_service.list_blobs(container_name) if re.match(r'tagging_(.*).csv', blob.name)]
    if file_date:
        block_blob_service.get_blob_to_path(container_name, max(file_date, key=lambda x:x[1])[0], "totag_tagging.csv")
    create_vott_json("totag", int(sys.argv[1]), config_file["user_folders"]=="True", config_file["pick_max"]=="True", "", config_file["tagging_location"], 
                blob_credentials=(block_blob_service, container_name), tag_names=config_file["classes"].split(","))
    container_name = config_file["label_container_name"]
    block_blob_service.create_blob_from_path(container_name, "{}_{}.{}".format("tagging",int(time.time() * 1000),"csv"), "totag_tagging.csv")
    block_blob_service.create_blob_from_path(container_name, "{}_{}.{}".format("totag",int(time.time() * 1000),"csv"), "totag_new.csv")

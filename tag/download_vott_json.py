import csv
import json
from collections import defaultdict
from heapq import nlargest, nsmallest
from typing import List, Tuple, Dict
from pathlib import Path
import shutil
import random
import colorsys
import numpy as np

CONFIDENCE_LOCATION = -1
TAG_CONFIDENCE_LOCATION = -2
FILENAME_LOCATION = 0
FOLDER_LOCATION = 8
HEIGHT_LOCATION = 6
WIDTH_LOCATION = 7
TAG_LOCATION = 1
TAG_STARTING_LOCATION = 2
# Should be equal to width_location
TAG_ENDING_LOCATION = 7

def make_vott_output(all_predictions, output_location, user_folders, image_loc, blob_credentials = None,
        tag_names: List[str] = ["stamp"], tag_colors: List[str] = "#ed1010", max_tags_per_pixel=None):
    shutil.rmtree(output_location, ignore_errors=True)
    if max_tags_per_pixel is not None:
        max_tags_per_pixel = int(max_tags_per_pixel)
    if user_folders:
        folder_name = Path(all_predictions[0][0][FOLDER_LOCATION]).name
        output_location = str(Path(output_location)/folder_name)
    else:
        output_location = str(Path(output_location)/"Images")
    using_blob_storage = blob_credentials is not None
    if using_blob_storage:
        output_location = Path(output_location)
        blob_service, container_name = blob_credentials
    else:
        image_loc = Path(image_loc)
    output_location.mkdir(parents=True, exist_ok=True)
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
            if image_loc:
                print(image_loc + "/" + prediction[0][FILENAME_LOCATION])
                blob_service.get_blob_to_path(container_name, image_loc + "/" + prediction[0][FILENAME_LOCATION],
                    str(output_location/prediction[0][FILENAME_LOCATION]))
            else:
                print(prediction[0][FILENAME_LOCATION])
                blob_service.get_blob_to_path(container_name, prediction[0][FILENAME_LOCATION],
                    str(output_location/prediction[0][FILENAME_LOCATION]))
        else:
            shutil.copy(str(image_loc/prediction[0][FILENAME_LOCATION]), output_location)
    all_predictions.sort(key=lambda x: x[0][FILENAME_LOCATION])
    dirjson = {}
    dirjson["frames"] = {}
    for i, predictions in enumerate(all_predictions):
        all_frames = []
        set_predictions = defaultdict(list)
        if max_tags_per_pixel is None:
            for prediction in predictions:
                x_1, x_2, y_1, y_2, height, width = map(float, prediction[TAG_STARTING_LOCATION:TAG_ENDING_LOCATION+1])
                if prediction[TAG_LOCATION]!="NULL" and (x_1,x_2,y_1,y_2)!=(0,0,0,0):
                    x_1 = int(x_1*width)
                    x_2 = int(x_2*width)
                    y_1 = int(y_1*height)
                    y_2 = int(y_2*height)
                    set_predictions[(x_1, x_2, y_1, y_2, height, width)].append(prediction[TAG_LOCATION])
        else:
            if predictions:
                num_tags = np.zeros((int(predictions[0][HEIGHT_LOCATION]),int(predictions[0][WIDTH_LOCATION])), dtype=int)
                for prediction in sorted(predictions, key=lambda x: float(x[TAG_CONFIDENCE_LOCATION]), reverse=True):
                    x_1, x_2, y_1, y_2, height, width = map(float, prediction[TAG_STARTING_LOCATION:TAG_ENDING_LOCATION+1])
                    if prediction[TAG_LOCATION]!="NULL" and (x_1,x_2,y_1,y_2)!=(0,0,0,0):
                        x_1 = int(x_1*width)
                        x_2 = int(x_2*width)
                        y_1 = int(y_1*height)
                        y_2 = int(y_2*height)
                        if np.amax(num_tags[y_1:y_2, x_1:x_2])<max_tags_per_pixel:
                            num_tags[y_1:y_2, x_1:x_2]+=1
                            set_predictions[(x_1, x_2, y_1, y_2, height, width)].append(prediction[TAG_LOCATION])
        for j,(coordinates, tags) in enumerate(set_predictions.items(), 1):
            # filename,tag,x1,x2,y1,y2,true_height,true_width,image_directory
            x_1, x_2, y_1, y_2, height, width = coordinates
            curframe = {}
            curframe["x1"] = x_1
            curframe["y1"] = y_1
            curframe["x2"] = x_2
            curframe["y2"] = y_2
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

def create_vott_json(file_location, num_rows, user_folders, pick_max, image_loc, output_location, blob_credentials=None, tag_names = ["stamp"], max_tags_per_pixel=None):
    all_files = get_top_rows(file_location, num_rows, user_folders, pick_max)
    # The tag_colors list generates random colors for each tag. To ensure that these colors stand out / are easy to see on a picture, the colors are generated
    # in the hls format, with the random numbers biased towards a high luminosity (>=.8) and saturation (>=.75).
    make_vott_output(all_files, output_location, user_folders, image_loc, blob_credentials=blob_credentials, tag_names=tag_names,
    tag_colors=['#%02x%02x%02x' % (int(256*r), int(256*g), int(256*b)) for 
            r,g,b in [colorsys.hls_to_rgb(random.random(),0.8 + random.random()/5.0, 0.75 + random.random()/4.0) for _ in tag_names]], max_tags_per_pixel=max_tags_per_pixel)

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
                blob_credentials=(block_blob_service, container_name), tag_names=config_file["classes"].split(","), max_tags_per_pixel=config_file.get("max_tags_per_pixel",None))
    container_name = config_file["label_container_name"]
    block_blob_service.create_blob_from_path(container_name, "{}_{}.{}".format("tagging",int(time.time() * 1000),"csv"), "totag_tagging.csv")
    block_blob_service.create_blob_from_path(container_name, "{}_{}.{}".format("totag",int(time.time() * 1000),"csv"), "totag_new.csv")

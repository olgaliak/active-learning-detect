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
from io import StringIO
from math import isclose

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
import blob_utils  as butils

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

random.seed(42)

def add_class_name(tag_names, name):
    if name not in tag_names:
        tag_names = tag_names + [name]
    return  tag_names

def remove_class_name(tag_names, name):
    if name in tag_names:
        tag_names.remove(name)
    return tag_names

def  add_bkg_class_name(tag_names):
    return add_class_name(tag_names, "NULL")

def remove_bkg_class_name(tag_names):
    return  remove_class_name(tag_names, "NULL")

def get_image_loc(prediction, user_folders, image_loc):
    if user_folders:
        if image_loc == "":
            image_loc = Path(prediction[0][FOLDER_LOCATION]).name
        else:
            image_loc = image_loc + "/" + Path(prediction[0][FOLDER_LOCATION]).name

    return image_loc

def get_output_location(prediction, user_folders, output_location_param):
    if user_folders:
        folder_name = Path(prediction[0][FOLDER_LOCATION]).name
        output_location = Path(output_location_param)/folder_name
    else:
        output_location = Path(output_location_param)/"Images"
    return output_location

def make_vott_output(all_predictions, output_location_param, user_folders, image_loc_param, blob_credentials = None,
        tag_names: List[str] = ["stamp"], tag_colors: List[str] = "#ed1010", max_tags_per_pixel=None):
    if max_tags_per_pixel is not None:
        max_tags_per_pixel = int(max_tags_per_pixel)

    tag_names = remove_bkg_class_name(tag_names)

    # The tag_colors list generates random colors for each tag. To ensure that these colors stand out / are easy to see on a picture, the colors are generated
    # in the hls format, with the random numbers biased towards a high luminosity (>=.8) and saturation (>=.75).
    if tag_colors is None:
        tag_colors = ['#%02x%02x%02x' % (int(256*r), int(256*g), int(256*b)) for
            r,g,b in [colorsys.hls_to_rgb(random.random(),0.8 + random.random()/5.0, 0.75 + random.random()/4.0) for _ in tag_names]]

    using_blob_storage = blob_credentials is not None

    dict_predictions_per_folder =   {} #defaultdict(list)
    i = 0
    n_err = 0
    for prediction in all_predictions[:]:
        #print(i)
        image_loc = get_image_loc(prediction, user_folders, image_loc_param)
        output_location = get_output_location(prediction, user_folders, output_location_param)
        if output_location not in dict_predictions_per_folder:
            output_location.mkdir(parents=True, exist_ok=True)
            dict_predictions_per_folder[output_location] = []
            print("Created dir ", str(output_location))
        if using_blob_storage:
            blob_dest = str(output_location / prediction[0][FILENAME_LOCATION])
            if image_loc:
                blob_name = image_loc + "/" + prediction[0][FILENAME_LOCATION]
            else:
                blob_name = prediction[0][FILENAME_LOCATION]

            if not butils.attempt_get_blob(blob_credentials, blob_name, blob_dest):
                all_predictions.remove(prediction)
                n_err = n_err + 1
                continue;
        else:
            shutil.copy(os.path.join(image_loc, prediction[0][FILENAME_LOCATION]), str(output_location))

        dict_predictions_per_folder[output_location].append(prediction)
        i = i + 1

    print("Dowloaded {0} files. Number of errors: {1}".format(i, n_err))

#TBD: enum through dict and make json per folder!
    for output_location, folder_predictions in dict_predictions_per_folder.items():
        folder_predictions.sort(key=lambda x: x[0][FILENAME_LOCATION])
        dirjson = {}
        dirjson["frames"] = {}
        for i, predictions in enumerate(folder_predictions):
            all_frames = []
            file_name = ""
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
                        file_name = prediction[FILENAME_LOCATION]
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
                                file_name = prediction[FILENAME_LOCATION]
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
            dirjson["frames"][file_name] = all_frames
        dirjson["framerate"] = "1"
        dirjson["inputTags"] = ",".join(tag_names)
        dirjson["suggestiontype"] = "track"
        dirjson["scd"] = False
        dirjson["tag_colors"] = tag_colors
        with open(str(output_location)+".json","w") as json_out:
            json.dump(dirjson, json_out, sort_keys = True)


def select_rows(arr_image_data, num_rows, is_largest):
    total_rows = len(arr_image_data)
    if num_rows > total_rows:
        num_rows = total_rows
    if is_largest:
        top = nlargest(num_rows, arr_image_data,
                       key=lambda x: float(x[0][CONFIDENCE_LOCATION]))
    else:
        top = nsmallest(num_rows, arr_image_data,
                       key=lambda x: float(x[0][CONFIDENCE_LOCATION]))

    return top

def prepare_per_class_dict(all_files_per_folder, class_balances_cnt, tag_names):
    #result = {}
    result = defaultdict(list)
    for k, v in all_files_per_folder.items():
        v_arr = np.array(v)
        classes = v_arr[:, TAG_LOCATION]
        for i in range(class_balances_cnt):
            class_i = tag_names[i]
            if class_i in classes:
                result[class_i].append(v)

    return result


def parse_class_balance_setting(config_value, expected_cnt):
    print("Ideal class balance (from config):", config_value)
    if config_value is None:
        return  None
    arr_np = np.genfromtxt(StringIO(config_value), dtype=float, delimiter=',', loose=True)
    # check f there were non valid numbers
    if np.isnan(arr_np.any()):
        print("Found NaNs in ideal balance settings:", config_value)
        return None
    else:
        if (arr_np.size != expected_cnt):
            print("Size of ideal balance settings {0} is {1}. Expected {2}".format(arr_np.size, arr_np, expected_cnt))
            return None

        s = np.sum(arr_np)
        if  isclose(s, 1, abs_tol=0.01):
            return arr_np
        else:
            print("Sum of balance settings {0} should add up to 1: {1}".format(config_value, s) )


def filter_top(top, unmapclass_list, tag_names, class_map_dict, default_class):
    for im in top:
        for obj in im[:]:
            obj_init_class = obj[TAG_LOCATION]
            # remove bboxes for classes we are not interested in
            if obj_init_class in unmapclass_list:
                im.remove(obj)
            # assign new name to class
            if obj_init_class in tag_names:
                obj[TAG_LOCATION] = class_map_dict[obj_init_class]
            else:
                obj[TAG_LOCATION] = default_class

    return top

def get_top_rows(file_location_totag, num_rows, user_folders, pick_max, tag_names, ideal_class_balance, func_filter_top = None, *args):
    with file_location_totag.open(mode='r') as file:
        reader = csv.reader(file)
        header = next(reader)
        totag_list = list(reader)

    all_files = defaultdict(lambda: defaultdict(list))
    if user_folders:
        for row in totag_list:
            all_files[row[FOLDER_LOCATION]][row[0]].append(row)
    else:
        for row in totag_list:
            all_files['default_folder'][row[0]].append(row)
    selected_rows = []
    class_balances_cnt = 1
    if ideal_class_balance is not None:
        class_balances_cnt = len(ideal_class_balance)


    for folder_name in all_files:
        if ideal_class_balance is not None:
            all_files_per_class = prepare_per_class_dict(all_files[folder_name], class_balances_cnt, tag_names)
            for i in range(class_balances_cnt):
                num_rows_i = round(num_rows * float(ideal_class_balance[i]))
                class_i = tag_names[i]
                top = select_rows(all_files_per_class[class_i], num_rows_i, is_largest = pick_max)

                # drop values we selected from the dict
                # the same image may have object from diff classes
                for j in range(class_balances_cnt):
                    class_j = tag_names[j]
                    all_files_per_class[class_j] = [v for  v in all_files_per_class[class_j]
                                       if v not in top]

                if func_filter_top is not None:
                    top =  func_filter_top(top, *args) #func_filter_top(top, unmapclass_list, tag_names, class_map_dict, default_class)
                selected_rows = selected_rows + top
        else:
             top = select_rows(all_files[folder_name].values(), num_rows, is_largest = pick_max)
             if func_filter_top is not None:
                 top = func_filter_top(top, args)
             selected_rows = selected_rows + top
    return selected_rows, totag_list, header

def write_tag_csvs(selected_rows, totag_list, file_location_totag, file_location_togging, header):
    selected_filenames = {row[0][FILENAME_LOCATION] for row in selected_rows}
    file_exists = file_location_togging.is_file()
    with file_location_totag.open(mode='w', newline='') as totag, file_location_togging.open(mode='a', newline='') as tagging:
        totag_writer, tagging_writer = csv.writer(totag), csv.writer(tagging)
        totag_writer.writerow(header)
        if not file_exists:
            tagging_writer.writerow(header)
        for row in totag_list:
            (tagging_writer if row[FILENAME_LOCATION] in selected_filenames else totag_writer).writerow(row)


def create_init_vott_json(file_location, num_rows, user_folders, pick_max, image_loc, output_location, blob_credentials,
                     tag_names, new_tag_names, max_tags_per_pixel=None, config_class_balance=None, colors=None, *args):
    print("Creting VOTT json using pre-init classes")
    file_location_init_totag = (file_location / "init_totag.csv")
    file_location_tagging = (file_location / "tagging.csv")
    file_location_totag = (file_location / "totag.csv")
    selected_rows, totag_list, header = get_top_rows(file_location_init_totag, num_rows, user_folders, pick_max, tag_names,
                                                     config_class_balance, filter_top, *args)

    write_tag_csvs(selected_rows, totag_list, file_location_init_totag, file_location_tagging, header)
    write_tag_csvs(selected_rows, totag_list, file_location_totag, file_location_tagging, header)

    default_class = args[-1]
    new_tag_names = add_class_name(new_tag_names, default_class)
    make_vott_output(selected_rows, output_location, user_folders, image_loc, blob_credentials=blob_credentials,
                     tag_names=new_tag_names, tag_colors=colors, max_tags_per_pixel=max_tags_per_pixel)


def create_vott_json(file_location, num_rows, user_folders, pick_max, image_loc, output_location, blob_credentials=None,
                     tag_names = ["stamp"], max_tags_per_pixel=None, config_class_balance=None, colors = None):
    file_location_totag = (file_location / "totag.csv")
    file_location_togging = (file_location / "tagging.csv")
    selected_rows, totag_list, header = get_top_rows(file_location_totag, num_rows, user_folders, pick_max, tag_names, config_class_balance)

    write_tag_csvs(selected_rows, totag_list, file_location_totag, file_location_togging, header)

    make_vott_output(selected_rows, output_location, user_folders, image_loc, blob_credentials=blob_credentials,
                     tag_names= tag_names,  tag_colors=colors, max_tags_per_pixel=max_tags_per_pixel)

if __name__ == "__main__":
    if len(sys.argv)<3:
        raise ValueError("Need to specify number of images (first arg) and config file (second arg). Optionally provide psth to init_classes_map.json")
    config_file = Config.parse_file(sys.argv[2])
    block_blob_service = BlockBlobService(account_name=config_file["AZURE_STORAGE_ACCOUNT"], account_key=config_file["AZURE_STORAGE_KEY"])
    container_name = config_file["label_container_name"]
    shutil.rmtree(config_file["tagging_location"], ignore_errors=True)
    csv_file_loc = Path(config_file["tagging_location"])
    #csv_file_loc =  #Path("test_totag.csv")
    csv_file_loc.mkdir(parents=True, exist_ok=True)

    if len(sys.argv)>3 and 'json' in sys.argv[3].lower():
        print("Using init flow and class mapping json")
        json_fn = sys.argv[3]
        with open(json_fn, "r") as read_file:
            json_config = json.load(read_file)
        classmap = json_config["classmap"]
        ideal_balance_list = []
        new_tag_names = []
        init_tag_names = []
        class_map_dict = {}
        for m in classmap:
            ideal_balance_list.append(m['balance'])
            new_tag_names.append(m['map'])
            init_tag_names.append(m['initclass'])
            class_map_dict[m['initclass']] = m['map']
        ideal_balance = ','.join(ideal_balance_list)
        unmapclass_list = json_config["unmapclass"]
        default_class = json_config["default_class"]
        file_location_totag = csv_file_loc / "init_totag.csv"
        new_tag_names = add_bkg_class_name(new_tag_names)
        ideal_class_balance = parse_class_balance_setting(ideal_balance, len(new_tag_names))

        file_date = [(blob.name, blob.properties.last_modified) for blob in
                     block_blob_service.list_blobs(container_name) if re.match(r'init_totag_(.*).csv', blob.name)]
        block_blob_service.get_blob_to_path(container_name, max(file_date, key=lambda x: x[1])[0],
                                            str(file_location_totag))

        create_init_vott_json(csv_file_loc, int(sys.argv[1]), config_file["user_folders"] == "True",
                         config_file["pick_max"] == "True", "",
                         config_file["tagging_location"], (block_blob_service, config_file["image_container_name"]),
                         init_tag_names,
                         new_tag_names,
                         config_file.get("max_tags_per_pixel"),
                         ideal_class_balance,
                         None, #colors
                         unmapclass_list, init_tag_names, class_map_dict, default_class)

    else:
        file_date = [(blob.name, blob.properties.last_modified) for blob in
                     block_blob_service.list_blobs(container_name) if re.match(r'totag_(.*).csv', blob.name)]
        block_blob_service.get_blob_to_path(container_name, max(file_date, key=lambda x: x[1])[0],
                                            str(csv_file_loc / "totag.csv"))
        file_date = [(blob.name, blob.properties.last_modified) for blob in
                     block_blob_service.list_blobs(container_name) if re.match(r'tagging_(.*).csv', blob.name)]
        ideal_class_balance = config_file["ideal_class_balance"].split(",")
        if file_date:
            block_blob_service.get_blob_to_path(container_name, max(file_date, key=lambda x: x[1])[0],
                                                str(csv_file_loc / "tagging.csv"))
        tag_names = add_bkg_class_name(config_file["classes"].split(","))
        ideal_class_balance = parse_class_balance_setting(config_file.get("ideal_class_balance"), len(tag_names))
        create_vott_json(csv_file_loc, int(sys.argv[1]), config_file["user_folders"]=="True", config_file["pick_max"]=="True", "",
                     config_file["tagging_location"], blob_credentials=(block_blob_service, config_file["image_container_name"]),
                     tag_names= tag_names,
                     max_tags_per_pixel=config_file.get("max_tags_per_pixel"),
                     config_class_balance = ideal_class_balance)
    container_name = config_file["label_container_name"]
    block_blob_service.create_blob_from_path(container_name, "{}_{}.{}".format("tagging",int(time.time() * 1000),"csv"), str(csv_file_loc/"tagging.csv"))
    block_blob_service.create_blob_from_path(container_name, "{}_{}.{}".format("totag",int(time.time() * 1000),"csv"), str(csv_file_loc/"totag.csv"))

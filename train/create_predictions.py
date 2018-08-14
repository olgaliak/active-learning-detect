from functools import reduce
from pathlib import Path
from typing import List, Tuple, Dict, AbstractSet
import json
import cv2
import csv
from collections import defaultdict

FOLDER_LOCATION=8

def calculate_confidence(predictions):
    return min([float(prediction[0]) for prediction in predictions])

def make_csv_output(all_predictions: List[List[List[int]]], all_names: List[str], all_sizes: List[Tuple[int]], 
        tagged_output: str, untagged_output: str, file_set: AbstractSet, user_folders: bool = True):
    '''
    Convert list of Detector class predictions as well as list of image sizes
    into a dict matching the VOTT json format.
    '''
    with open(tagged_output, 'w', newline='') as tagged_file, open(untagged_output, 'w', newline='') as untagged_file:
        tagged_writer = csv.writer(tagged_file)
        untagged_writer = csv.writer(untagged_file)
        if user_folders:
            tagged_writer.writerow(["filename", "class", "xmin","xmax","ymin","ymax","height","width","folder", "confidence"])
            untagged_writer.writerow(["filename", "class", "xmin","xmax","ymin","ymax","height","width","folder", "confidence"])
        else:
            tagged_writer.writerow(["filename", "class", "xmin","xmax","ymin","ymax","height","width","confidence"])
            untagged_writer.writerow(["filename", "class", "xmin","xmax","ymin","ymax","height","width","confidence"])
        if user_folders:
            for (folder, name), predictions, (height, width) in zip(all_names, all_predictions, all_sizes):
                if not predictions:
                    predictions = [[0,"NULL",0,0,0,0]]
                confidence = calculate_confidence(predictions)
                for prediction in predictions:
                    (tagged_writer if name in file_set[folder] else untagged_writer).writerow([name,prediction[1],prediction[3],prediction[5],prediction[2],prediction[4],height,width,folder,confidence])
        else:
            for name, predictions, (height,width) in zip(all_names, all_predictions, all_sizes):
                if not predictions:
                    predictions = [[0,"NULL",0,0,0,0]]
                confidence = calculate_confidence(predictions)
                for prediction in predictions:
                    (tagged_writer if name in file_set else untagged_writer).writerow([name,prediction[1],prediction[3],prediction[5],prediction[2],prediction[4],height,width,confidence])

def get_suggestions(detector, basedir: str, untagged_output: str, 
    tagged_output: str, cur_tagged: str, cur_tagging: str, min_confidence: float =.2,
    image_size: Tuple=(1200,1550), filetype: str="*.jpg", minibatchsize: int=50,
    user_folders: bool=True):
    '''Gets suggestions from a given detector and uses them to generate VOTT tags
    
    Function inputs an instance of the Detector class along with a directory,
    and optionally a confidence interval, image size, and tag information (name and color). 
    It returns a list of subfolders in that directory sorted by how confident the 
    given Detector was was in predicting bouding boxes on files within that subfolder.
    It also generates VOTT JSON tags corresponding to the predicted bounding boxes.
    The optional confidence interval and image size correspond to the matching optional
    arguments to the Detector class
    '''
    basedir = Path(basedir)
    CV2_COLOR_LOAD_FLAG = 1
    all_predictions = []
    if user_folders:
        # TODO: Cross reference with ToTag
        # download latest tagging and tagged
        with open(cur_tagged, 'r') as file:
            reader = csv.reader(file)
            next(reader, None)
            all_tagged = list(reader)
        with open(cur_tagging, 'r') as file:
            reader = csv.reader(file)
            next(reader, None)
            all_tagged.extend(list(reader))
        already_tagged = defaultdict(set)
        for row in all_tagged:
            already_tagged[row[FOLDER_LOCATION]].add(row[0])
        subdirs = [subfile for subfile in basedir.iterdir() if subfile.is_dir()]
        all_names = []
        all_sizes = []
        all_images = []
        for subdir in subdirs:
            cur_image_names = list(subdir.rglob(filetype))
            cur_images = [cv2.imread(str(image_name), CV2_COLOR_LOAD_FLAG) for image_name in cur_image_names]
            all_sizes += [image.shape[:2] for image in cur_images]
            all_images += [cv2.resize(cv2_image, image_size) for cv2_image in cur_images]
            foldername = subdir.stem
            all_names += [(foldername, filename.name) for filename in cur_image_names]
        all_predictions = detector.predict(all_images, min_confidence=min_confidence)
    else:
        with open(cur_tagged, 'r') as file:
            reader = csv.reader(file)
            next(reader, None)
            already_tagged = {row[0] for row in reader}
        with open(cur_tagging, 'r') as file:
            reader = csv.reader(file)
            next(reader, None)
            already_tagged |= {row[0] for row in reader}
        all_names = list(basedir.rglob(filetype))
        all_images = [cv2.imread(str(image_name), CV2_COLOR_LOAD_FLAG) for image_name in all_names]
        all_sizes = [image.shape[:2] for image in all_images]
        all_images = [cv2.resize(cv2_image, image_size) for cv2_image in all_images]
        all_names = [filename.name for filename in all_names]
        all_predictions = detector.predict(all_images, min_confidence=min_confidence)
    make_csv_output(all_predictions, all_names, all_sizes, untagged_output, tagged_output, already_tagged, user_folders)

if __name__ == "__main__":
    from azure.storage.blob import BlockBlobService
    from tf_detector import TFDetector
    import re
    import sys
    sys.path.append("..")
    from utils.config import Config
    config_file = Config.parse_file("config.ini")
    image_dir = config_file["image_dir"]
    untagged_output = config_file["untagged_output"]
    tagged_output = config_file["tagged_predictions"]
    block_blob_service = BlockBlobService(account_name=config_file["AZURE_STORAGE_ACCOUNT"], account_key=config_file["AZURE_STORAGE_KEY"])
    container_name = config_file["label_container_name"]
    file_date = [(blob.name, blob.properties.last_modified) for blob in block_blob_service.list_blobs(container_name) if re.match(r'tagged_(.*).csv', blob.name)]
    block_blob_service.get_blob_to_path(container_name, max(file_date, key=lambda x:x[1])[0], "tagged.csv")
    file_date = [(blob.name, blob.properties.last_modified) for blob in block_blob_service.list_blobs(container_name) if re.match(r'tagging_(.*).csv', blob.name)]
    block_blob_service.get_blob_to_path(container_name, max(file_date, key=lambda x:x[1])[0], "tagging.csv")
    cur_detector = TFDetector(config_file["classes"].split(","), str(Path(config_file["inference_output_dir"])/"frozen_inference_graph.pb"))
    get_suggestions(cur_detector, image_dir, untagged_output, tagged_output, "tagged.csv", "tagging.csv", filetype=config_file["filetype"], min_confidence=float(config_file["min_confidence"]), user_folders=config_file["user_folders"]=="True")

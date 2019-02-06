from functools import reduce
from pathlib import Path
from typing import List, Tuple, Dict, AbstractSet
import json
import cv2
import csv
from collections import defaultdict
import numpy as np

CV2_COLOR_LOAD_FLAG = 1

NUM_CHANNELS=3
FOLDER_LOCATION=8

PREDICTIONS_SCHEMA = \
    ["filename", "class", "xmin","xmax","ymin","ymax","height","width","folder", "box_confidence", "image_confidence"]
PREDICTIONS_SCHEMA_NO_FOLDER =\
    ["filename", "class", "xmin","xmax","ymin","ymax","height","width","box_confidence", "image_confidence"]

#name,prediction[CLASS_IDX],prediction[XMIN_IDX],prediction[XMAX_IDX],prediction[YMIN_IDX],prediction[YMAX_IDX],height,width,folder,prediction[BOX_CONFID_IDX], confidence
BOX_CONFID_IDX = 0
FILENAME_LOCATION = 0
CLASS_IDX = 1
XMIN_IDX = 3
XMAX_IDX = 5
YMIN_IDX = 2
YMAX_IDX = 4


def calculate_confidence(predictions):
    return min([float(prediction[0]) for prediction in predictions])

def make_csv_output(all_predictions: List[List[List[int]]], all_names: List[str], all_sizes: List[Tuple[int]], 
        untagged_output: str, tagged_output: str, file_set: AbstractSet, user_folders: bool = True):
    '''
    Convert list of Detector class predictions as well as list of image sizes
    into a dict matching the VOTT json format.
    '''
    with open(tagged_output, 'w', newline='') as tagged_file, open(untagged_output, 'w', newline='') as untagged_file:
        tagged_writer = csv.writer(tagged_file)
        untagged_writer = csv.writer(untagged_file)
        if user_folders:
            tagged_writer.writerow(PREDICTIONS_SCHEMA)
            untagged_writer.writerow(PREDICTIONS_SCHEMA)
        else:
            tagged_writer.writerow(PREDICTIONS_SCHEMA_NO_FOLDER)
            untagged_writer.writerow(PREDICTIONS_SCHEMA_NO_FOLDER)
        if user_folders:
            for (folder, name), predictions, (height, width) in zip(all_names, all_predictions, all_sizes):
                if not predictions:
                    predictions = [[0,"NULL",0,0,0,0]]
                confidence = calculate_confidence(predictions)
                for prediction in predictions:
                    (tagged_writer if name in file_set[folder] else untagged_writer).writerow([
                        name,
                        prediction[CLASS_IDX],prediction[XMIN_IDX],prediction[XMAX_IDX],
                        prediction[YMIN_IDX],prediction[YMAX_IDX],height,width,
                        folder,
                        prediction[BOX_CONFID_IDX], confidence])
        else:
            for name, predictions, (height,width) in zip(all_names, all_predictions, all_sizes):
                if not predictions:
                    predictions = [[0,"NULL",0,0,0,0]]
                confidence = calculate_confidence(predictions)
                for prediction in predictions:
                    (tagged_writer if name in file_set else untagged_writer).writerow([
                            name,
                            prediction[CLASS_IDX], prediction[XMIN_IDX], prediction[XMAX_IDX],
                            prediction[YMIN_IDX], prediction[YMAX_IDX], height, width,
                            prediction[BOX_CONFID_IDX], confidence])
    print(untagged_output, tagged_output)

def get_images_for_prediction(subdir, filetype, already_tagged_this_folder, image_size):
    '''
    Function walks though the given directory of images and consucts ndarrays of image data that will be
    used to get model's predictions (for subsequent review by human annotators).
    Images that  already have been reviewed (tagged) are excluded from the list.
    :param subdir: local directory where images are
    :param filetype: extension of the images
    :param already_tagged_this_folder: list of images (names), that already have been tagged and thus can be skiepped
    :param image_size: target image size
    :return: function retuns 3 arrays
       - all_images_this_folder -- ndarray representation of image
       - all_names_this_folder  -- names of the images that will get pre-tagged,
       - all_sizes_this_folder  -- original size of images
    '''
    all_image_files = []
    cur_image_names = list(subdir.rglob(filetype))
    print("Total image names: ", len(cur_image_names))
    all_image_files += [str(image_name) for image_name in cur_image_names]
    foldername = subdir.stem
    all_nonfilt_names = [(foldername, filename.name) for filename in cur_image_names]

    # check if images have been tagged already
    print("Already tagged {0} images in folder {1}.".format(len(already_tagged_this_folder), foldername))
    all_names_this_folder = [t for t in all_nonfilt_names if t[1] not in already_tagged_this_folder]
    print("{0} images are taken for prediction from folder {1}".format(len(all_names_this_folder), foldername))

    all_filt_imagepaths = [filepath for filepath in cur_image_names if filepath.name not in already_tagged_this_folder]

    # Reversed because numpy is row-major
    all_sizes_this_folder = [cv2.imread(str(image_path), CV2_COLOR_LOAD_FLAG).shape[:2] for image_path in
                             all_filt_imagepaths]
    all_images_this_folder = np.zeros((len(all_names_this_folder), *reversed(image_size), NUM_CHANNELS), dtype=np.uint8)
    for curindex, image_path in enumerate(all_filt_imagepaths):
        all_images_this_folder[curindex] = cv2.resize(cv2.imread(str(image_path), CV2_COLOR_LOAD_FLAG), image_size)

    return all_images_this_folder, all_names_this_folder, all_sizes_this_folder

def get_suggestions(detector, basedir: str, untagged_output: str, 
    tagged_output: str, cur_tagged: str, cur_tagging: str, min_confidence: float =.2,
    image_size: Tuple=(1000,750), filetype: str="*.jpg", minibatchsize: int=16,
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
    all_images = None
    all_tagged = []
    all_names = []
    if user_folders:
        # TODO: Cross reference with ToTag
        # download latest tagging and tagged
        if cur_tagged is not None:
            with open(cur_tagged, 'r') as file:
                reader = csv.reader(file)
                next(reader, None)
                all_tagged = list(reader)
        if cur_tagging is not None:
            with open(cur_tagging, 'r') as file:
                reader = csv.reader(file)
                next(reader, None)
                all_tagged.extend(list(reader))
        already_tagged = defaultdict(set)
        for row in all_tagged:
            already_tagged[row[FOLDER_LOCATION]].add(row[FILENAME_LOCATION])
        print("Already tagged {0} images.".format(sum(map(len, already_tagged.values()))))
        subdirs = [subfile for subfile in basedir.iterdir() if subfile.is_dir()]
        print("subdirs: ", subdirs)
        all_sizes = []
        for subdir in subdirs:
            foldername = subdir.stem
            already_tagged_this_folder = already_tagged[foldername]
            all_images_this_folder, all_names_this_folder, all_sizes_this_folder =\
                get_images_for_prediction(subdir, filetype, already_tagged_this_folder, image_size)

            all_names += all_names_this_folder
            if (all_images == None):
                all_images = all_images_this_folder
            else:
                all_images = np.concatenate((all_images,all_images_this_folder), axis=0)
            all_sizes += all_sizes_this_folder

        print("Shape of all_images: ", all_images.shape)
        all_predictions = detector.predict(all_images, min_confidence=min_confidence, batch_size=minibatchsize)
    else:
        with open(cur_tagged, 'r') as file:
            reader = csv.reader(file)
            next(reader, None)
            already_tagged = {row[0] for row in reader}
        with open(cur_tagging, 'r') as file:
            reader = csv.reader(file)
            next(reader, None)
            already_tagged |= {row[0] for row in reader}

        already_tagged_this_folder = already_tagged
        all_images, all_names, all_sizes = \
            get_images_for_prediction(basedir, filetype, already_tagged_this_folder, image_size)
        all_predictions = detector.predict(all_images, batch_size=1, min_confidence=min_confidence)
    make_csv_output(all_predictions, all_names, all_sizes, untagged_output, tagged_output, already_tagged, user_folders)

if __name__ == "__main__":
    from azure.storage.blob import BlockBlobService
    from tf_detector import TFDetector
    import re
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
    image_dir = config_file["image_dir"]
    untagged_output = config_file["untagged_output"]
    tagged_output = config_file["tagged_predictions"]
    block_blob_service = BlockBlobService(account_name=config_file["AZURE_STORAGE_ACCOUNT"], account_key=config_file["AZURE_STORAGE_KEY"])
    container_name = config_file["label_container_name"]
    file_date = [(blob.name, blob.properties.last_modified) for blob in block_blob_service.list_blobs(container_name) if re.match(r'tagged_(.*).csv', blob.name)]
    cur_tagged = None
    cur_tagging = None
    classes = []
    model = None
    if len(sys.argv) > 3 and (sys.argv[2].lower() =='init_pred'):
        print("Using MS COCO pretrained model to detect known 90 classes. For class id <-> name mapping check this file: https://github.com/tensorflow/models/blob/master/research/object_detection/data/mscoco_label_map.pbtxt")
        model = sys.argv[3]
        print("Using model: " + model)
        classesIDs = list(range(1, 91))
        classes = [str(x) for x in classesIDs]
    else:
        classes = config_file["classes"].split(",")
        model = str(Path(config_file["inference_output_dir"])/"frozen_inference_graph.pb")
        print("using model: ", model)
        if file_date:
            block_blob_service.get_blob_to_path(container_name, max(file_date, key=lambda x:x[1])[0], "tagged.csv")
            cur_tagged = "tagged.csv"
        file_date = [(blob.name, blob.properties.last_modified) for blob in block_blob_service.list_blobs(container_name) if re.match(r'tagging_(.*).csv', blob.name)]
        if file_date:
            block_blob_service.get_blob_to_path(container_name, max(file_date, key=lambda x:x[1])[0], "tagging.csv")
            cur_tagging = "tagging.csv"

    cur_detector = TFDetector(classes, model)
    get_suggestions(cur_detector, image_dir, untagged_output, tagged_output, cur_tagged, cur_tagging, filetype=config_file["filetype"], min_confidence=float(config_file["min_confidence"]), user_folders=config_file["user_folders"]=="True")

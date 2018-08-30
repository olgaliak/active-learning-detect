import numpy as np
import cv2
import csv
from collections import defaultdict
from functools import partial
from pathlib import Path
HEIGHT, WIDTH = 1000, 1000
FILENAME_LOCATION=0
FOLDER_LOCATION=8
CLASS_LOCATION=1
PREDS_START=2
PREDS_END=5
BOX_CONFIDENCE_LOCATION=-2
def detectortest(predictions, ground_truths, output, user_folders):
    '''Inputs test_detector that follows the Detector ABC, images which is
    a list of image filenames, image_size which is the resized image size
    necessary for inputting and ground_truths which is the correct labels
    for the images. Optionally takes in min_fscore.
    Outputs a boolean based on whether or not the F1-Score
    of test_detector was greater than min_fscore'''
    all_detector_preds = defaultdict(lambda: defaultdict(list))
    with open(predictions, 'r') as preds_file:
        reader = csv.reader(preds_file)
        next(reader, None)
        if user_folders:
            for row in reader:
                all_detector_preds[(row[FOLDER_LOCATION], row[FILENAME_LOCATION])][row[CLASS_LOCATION]].append(row[PREDS_START:PREDS_END+1]+row[BOX_CONFIDENCE_LOCATION:BOX_CONFIDENCE_LOCATION+1])
        else:
            for row in reader:
                all_detector_preds[row[FILENAME_LOCATION]][row[CLASS_LOCATION]].append(row[PREDS_START:PREDS_END+1]+row[BOX_CONFIDENCE_LOCATION:BOX_CONFIDENCE_LOCATION+1])
    all_gtruths = defaultdict(lambda: defaultdict(list))
    with open(ground_truths, 'r') as truths_file:
        reader = csv.reader(truths_file)
        next(reader, None)
        if user_folders:
            for row in reader:
                all_gtruths[(row[FOLDER_LOCATION], row[FILENAME_LOCATION])][row[CLASS_LOCATION]].append(row[PREDS_START:PREDS_END+1])
        else:
            for row in reader:
                all_gtruths[row[FILENAME_LOCATION]][row[CLASS_LOCATION]].append(row[PREDS_START:PREDS_END+1])
    precisions = []
    recalls = []
    for filename in all_gtruths:
        file_precisions = []
        file_recalls = []
        for classname, ground_preds in all_gtruths[filename].items():
            ground_truth = np.zeros((HEIGHT, WIDTH))
            for xmin,xmax,ymin,ymax in map(partial(map, float), ground_preds):
                ground_truth[int(ymin*HEIGHT):int(ymax*HEIGHT), int(xmin*WIDTH):int(xmax*WIDTH)] = 1
            det_preds = all_detector_preds[filename][classname]
            detection = np.zeros((HEIGHT, WIDTH))
            for xmin,xmax,ymin,ymax in map(partial(map, float), det_preds):
                detection[int(ymin*HEIGHT):int(ymax*HEIGHT), int(xmin*WIDTH):int(xmax*WIDTH)] = 1
            ground_area = ground_truth.sum()
            detect_area = detection.sum()
            inter_area = (ground_truth * detection).sum()
            precision = inter_area / detect_area if detect_area!=0 else 1
            recall = inter_area / ground_area
            file_precisions.append(precision)
            file_recalls.append(recall)
        precisions.append(np.mean(file_precisions))
        recalls.append(np.mean(file_recalls))
    avg_prec = np.mean(precisions)
    avg_recall = np.mean(recalls)
    f1_score = 2 * avg_prec * avg_recall/(avg_prec + avg_recall)
    print("Average Precision: {}, Recall: {}, F1-Score: {}".format(avg_prec, avg_recall, f1_score))
    with open(output, 'w') as out_file:
        out_file.write("Average Precision: {}, Recall: {}, F1-Score: {}".format(avg_prec, avg_recall, f1_score))
if __name__ == "__main__":
    import re
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
    file_date = [(blob.name, blob.properties.last_modified) for blob in block_blob_service.list_blobs(container_name) if re.match(r'test_(.*).csv', blob.name)]
    if file_date:
        block_blob_service.get_blob_to_path(container_name, max(file_date, key=lambda x:x[1])[0], config_file["test_output"])
        detectortest(config_file["tagged_predictions"], config_file["test_output"], config_file["validation_output"], config_file["user_folders"]=="True")
    else:
        # TODO: If we keep track of val/train we can calc prec/f-score for that too
        detectortest(config_file["tagged_predictions"], config_file["tagged_output"], config_file["validation_output"], config_file["user_folders"]=="True")

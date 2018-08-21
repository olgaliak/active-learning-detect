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

def get_results(ground_arr, detector_arr, min_iou=.5):
    # Sort detector arr in descending confidence
    detector_arr = detector_arr[detector_arr[:,-1].argsort()[::-1]]
    det_x_min, det_x_max, det_y_min, det_y_max, _ = detector_arr.transpose()
    ground_x_min, ground_x_max, ground_y_min, ground_y_max = ground_arr.transpose()
    # Clip negative since negative implies no overlap
    intersect_widths = (np.minimum(det_x_max[:, np.newaxis], ground_x_max) - np.maximum(det_x_min[:, np.newaxis], ground_x_min)).clip(min=0)
    intersect_heights = (np.minimum(det_y_max[:, np.newaxis], ground_y_max) - np.maximum(det_y_min[:, np.newaxis], ground_y_min)).clip(min=0)
    intersect_areas = intersect_widths*intersect_heights
    # Inclusion exclusion principle!
    union_areas = ((det_x_max-det_x_min)*(det_y_max-det_y_min))[:, np.newaxis] + ((ground_x_max-ground_x_min)*(ground_y_max-ground_y_min)) - intersect_areas
    # Just in case a ground truth has zero area
    iou = np.divide(intersect_areas, union_areas, out=union_areas, where=union_areas!=0)
    num_gtruths = ground_arr.shape[0]
    num_detections = detector_arr.shape[0]
    best_gtruths = np.argmax(iou, axis=1)
    valid_gtruths = iou[np.arange(num_detections), best_gtruths]>min_iou
    num_true_positives = np.count_nonzero(np.bincount(best_gtruths[valid_gtruths]))
    num_false_positives = num_detections - detected_gtruths
    num_false_negatives = num_gtruths - detected_gtruths
    return num_true_positives, num_false_positives, num_false_negatives

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
            true_pos, false_pos, false_neg = get_results(np.asarray(ground_preds, dtype=np.float64), np.asarray(all_detector_preds[filename][classname], dtype=np.float64))
            
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

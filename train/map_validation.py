import numpy as np
import cv2
import csv
from collections import defaultdict
from functools import partial
from pathlib import Path
from pandas._libs.hashtable import unique_label_indices
HEIGHT, WIDTH = 1000, 1000
FILENAME_LOCATION=0
FOLDER_LOCATION=8
CLASS_LOCATION=1
PREDS_START=2
PREDS_END=5
BOX_CONFIDENCE_LOCATION=-2

def get_map_for_class(zipped_data_arr, min_ious=np.linspace(.50, 0.95, 10, endpoint=True),
            avg_recalls = np.linspace(0.00, 1.00, 101, endpoint=True)):
    # Used linspace over arange for min_ious/avg_recalls due to issues with endpoints
    all_confs = []
    all_correct_preds = []
    num_total_detections = 0
    num_total_gtruths = 0
    for ground_arr, detector_arr in zipped_data_arr:
        detector_arr = np.asarray(detector_arr, dtype=np.float64)
        ground_arr = np.asarray(ground_arr, dtype=np.float64)
        # Sort by descending confidence
        detector_arr = detector_arr[detector_arr[:,-1].argsort()[::-1]]
        det_x_min, det_x_max, det_y_min, det_y_max, confs = detector_arr.transpose()
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
        # Defined best ground truth as one with highest IOU
        best_gtruths = np.argmax(iou, axis=1)
        # Check that IOU is greater than min_IOU for all possible min_IOUs
        valid_preds = np.nonzero(iou[np.arange(num_detections), best_gtruths]>min_ious[:, np.newaxis])
        ## Useful for standard precision/recall metrics
        # num_true_positives = np.count_nonzero(np.bincount(best_gtruths[valid_preds]))
        # num_false_positives = num_detections - detected_gtruths
        # num_false_negatives = num_gtruths - detected_gtruths
        #
        # Uses pandas unique_label_indices to get leftmost index of each unique value in best_gtruths[valid_preds]
        # This is equivalent to finding the index of the highest confidence prediction box for each ground truth
        # which in turn is equivalent to finding the true positives (since we only consider the highest confidence
        # prediction for each ground truth to be a true positive, rest are false positives)
        # Note that pandas unique_label_indices is equivalent to np.unique(labels, return_index=True)[1] but
        # is considerably faster due to using a hashtable instead of sorting
        correct_preds = unique_label_indices(best_gtruths[valid_preds])
        # Finds original indices of correct predictions
        correct_preds = valid_preds[correct_preds]
        # Increments each index by the number of previous detections to map it to the correct index once
        # all the detections for each class are concatenated together
        correct_preds += num_total_detections
        all_correct_preds.append(correct_preds)
        all_confs.append(confs)
        num_total_detections += num_detections
        num_total_gtruths += num_gtruths
    # Concatenates all predictions and confidences together to find class MAP
    all_confs = np.concatenate(all_confs)
    all_correct_preds = np.concatenate(all_correct_preds, axis=1)
    # Sets only correct prediction indices to true, rest to false
    true_positives = np.zeros((num_total_detections, len(min_ious)), dtype=bool)
    true_positives[all_correct_preds] = True
    # Mergesort is chosen to be consistent with coco/matlab results
    sort_order = np.argsort(all_confs, kind='mergesort')[::-1]
    true_positives = true_positives[:,sort_order]
    # Keeps track of number of true positives until each given point
    all_true_positives = np.cumsum(true_positives, axis=1)
    # In python >=3 this is equivalent to np.true_divide
    precision = all_true_positives / np.arange(1, num_total_detections+1)
    # Makes each element in precision list max of all elements to right
    precision = np.maximum.accumulate(precision[:,::-1], axis=1)[:,::-1]
    recall = all_true_positives / num_total_gtruths
    # For each recall, finds leftmost index (i.e. largest precision) greater than it
    indices_to_average = np.apply_along_axis(np.searchsorted, 1, recall, avg_recalls)
    # Finds matching largest prediction for each recall and turns it into an array
    precs_to_average = precision[np.arange(len(precision))[:,np.newaxis], indices_to_average]
    # Returns average precision over each recall and over each IOU. Can specify an axis
    # if separate average precision is wanted for each IOU (e.g. to do more precise statistics)
    return np.mean(precs_to_average)

def detectortest(predictions, ground_truths, output, user_folders):
    '''Inputs test_detector that follows the Detector ABC, images which is
    a list of image filenames, image_size which is the resized image size
    necessary for inputting and ground_truths which is the correct labels
    for the images. Optionally takes in min_fscore.
    Outputs a boolean based on whether or not the F1-Score
    of test_detector was greater than min_fscore'''
    # First defaultdict corresponds to class name, inner one corresponds to filename, first list in tuple
    # corresponds to ground truths for that class+file and second list corresponds to predictions
    all_boxes = defaultdict(lambda: defaultdict(lambda: ([],[])))
    with open(ground_truths, 'r') as truths_file:
        reader = csv.reader(truths_file)
        next(reader, None)
        if user_folders:
            for row in reader:
                all_boxes[row[CLASS_LOCATION]][(row[FOLDER_LOCATION], row[FILENAME_LOCATION])][0].append(row[PREDS_START:PREDS_END+1])
        else:
            for row in reader:
                all_boxes[row[CLASS_LOCATION]][row[FILENAME_LOCATION]][0].append(row[PREDS_START:PREDS_END+1])
    with open(predictions, 'r') as preds_file:
        reader = csv.reader(preds_file)
        next(reader, None)
        if user_folders:
            for row in reader:
                all_boxes[row[CLASS_LOCATION]][(row[FOLDER_LOCATION], row[FILENAME_LOCATION])][1].append(row[PREDS_START:PREDS_END+1]+row[BOX_CONFIDENCE_LOCATION:BOX_CONFIDENCE_LOCATION+1])
        else:
            for row in reader:
                all_boxes[row[CLASS_LOCATION]][row[FILENAME_LOCATION]][1].append(row[PREDS_START:PREDS_END+1]+row[BOX_CONFIDENCE_LOCATION:BOX_CONFIDENCE_LOCATION+1])
    all_class_maps = {}
    for classname, all_file_preds in all_boxes.items():
        class_map = get_map_for_class(all_file_preds.values())
        all_class_maps[classname] = class_map
    # Calculates average over all classes. This is the mAP for the test set.
    avg_map = sum(all_class_maps.values())/len(all_class_maps) if all_class_maps else 0 
    print('Class Name: Average, Error: {}'.format(avg_map))
    print('\n'.join('Class Name: {}, Error: {}'.format(*classdata) for classdata in all_class_maps.items()))
    with open(output, 'w') as out_file:
        csv_writer=csv.writer(out_file)
        csv_writer.writerow(['Class Name','Error'])
        csv_writer.writerow(['Average', avg_map])
        for classdata in all_class_maps.items():
            csv_writer.writerow(classdata)
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

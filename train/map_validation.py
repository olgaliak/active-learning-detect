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
            avg_recalls = np.linspace(0.00, 1.00, 101, endpoint=True), nms_iou=.7):
    # Used linspace over arange for min_ious/avg_recalls due to issues with endpoints
    all_confs = []
    all_correct_preds = []
    num_total_detections = 0
    num_total_gtruths = 0
    for ground_arr, detector_arr in zipped_data_arr:
        num_gtruths = len(ground_arr)
        if not detector_arr:
            num_total_gtruths+=num_gtruths
            continue
        detector_arr = np.asarray(detector_arr, dtype=np.float64)
        # Sort by descending confidence, use mergesort to match COCO evaluation
        detector_arr = detector_arr[detector_arr[:,-1].argsort(kind='mergesort')[::-1]]
        det_x_min, det_x_max, det_y_min, det_y_max, confs = detector_arr.transpose()
        # Code for NMS
        all_indices_to_keep = []
        cur_indices_to_keep = np.arange(len(detector_arr))
        # Repeat until no detections left below overlap threshold
        while cur_indices_to_keep.size>1:
            # Add the most confident element
            all_indices_to_keep.append(cur_indices_to_keep[0])
            cur_x_min = det_x_min[cur_indices_to_keep]
            cur_x_max = det_x_max[cur_indices_to_keep]
            cur_y_min = det_y_min[cur_indices_to_keep]
            cur_y_max = det_y_max[cur_indices_to_keep]
            intersect_widths = (np.minimum(cur_x_max[0], cur_x_max[1:]) - np.maximum(cur_x_min[0], cur_x_min[1:])).clip(min=0)
            intersect_heights = (np.minimum(cur_y_max[0], cur_y_max[1:]) - np.maximum(cur_y_min[0], cur_y_min[1:])).clip(min=0)
            intersect_areas = intersect_widths*intersect_heights
            # Inclusion exclusion principle!
            union_areas = ((cur_x_max[0]-cur_x_min[0])*(cur_y_max[0]-cur_y_min[0]) + (cur_x_max[1:]-cur_x_min[1:])*(cur_y_max[1:]-cur_y_min[1:])) - intersect_areas
            # Just in case a ground truth has zero area
            cur_ious = np.divide(intersect_areas, union_areas, out=union_areas, where=union_areas!=0)
            # Keep appending [0] to a list
            # Just say cur_indices = np where cur_ious < nms_iou
            cur_indices_to_keep = cur_indices_to_keep[1:]
            cur_indices_to_keep = np.intersect1d(cur_indices_to_keep, cur_indices_to_keep[np.nonzero(cur_ious < nms_iou)[0]], assume_unique=True)
        detector_arr = detector_arr[np.asarray(all_indices_to_keep)]
        det_x_min, det_x_max, det_y_min, det_y_max, confs = detector_arr.transpose()
        num_detections = len(detector_arr)
        if not ground_arr:
            num_total_detections+=num_detections
            all_confs.append(confs)
            continue
        ground_arr = np.asarray(ground_arr, dtype=np.float64)
        ground_x_min, ground_x_max, ground_y_min, ground_y_max = ground_arr.transpose()
        # Clip negative since negative implies no overlap
        intersect_widths = (np.minimum(det_x_max[:, np.newaxis], ground_x_max) - np.maximum(det_x_min[:, np.newaxis], ground_x_min)).clip(min=0)
        intersect_heights = (np.minimum(det_y_max[:, np.newaxis], ground_y_max) - np.maximum(det_y_min[:, np.newaxis], ground_y_min)).clip(min=0)
        intersect_areas = intersect_widths*intersect_heights
        # Inclusion exclusion principle!
        union_areas = ((det_x_max-det_x_min)*(det_y_max-det_y_min))[:, np.newaxis] + ((ground_x_max-ground_x_min)*(ground_y_max-ground_y_min)) - intersect_areas
        # Just in case a ground truth has zero area
        iou = np.divide(intersect_areas, union_areas, out=union_areas, where=union_areas!=0)
        # Defined best ground truth as one with highest IOU. This is an array of size num_detections, where
        # best_gtruths[i] is the index of the ground truth to which prediction i is most similar (highest IOU)
        best_gtruths = np.argmax(iou, axis=1)
        # valid_preds is a generator where each element is a numpy int array. Each numpy array corresponds to
        # a min_iou in the min_ious array, and has indices corresponding to the predictions whose
        # prediction-ground truth pairs have IOU greater than that min_iou.
        valid_preds = map(np.nonzero, iou[np.arange(num_detections), best_gtruths]>min_ious[:, np.newaxis])
        #
        ## Useful for standard precision/recall metrics
        # num_true_positives = np.count_nonzero(np.bincount(best_gtruths[valid_preds]))
        # num_false_positives = num_detections - detected_gtruths
        # num_false_negatives = num_gtruths - detected_gtruths
        #
        # best_gtruths[valid_preds] uses the previously calculated valid_preds array to return an array 
        # containing the ground truths indices for each prediction whenever the ground truth-prediction
        # IOU was greater than min_iou. Then unique_label_indices is used to find the leftmost occuring
        # ground truth index for each ground truth index, which corresponds to finding the true positives
        # (since we only consider the highest confidence prediction for each ground truth to be a true
        # positive, rest are false positives)
        # Note that pandas unique_label_indices is equivalent to np.unique(labels, return_index=True)[1] but
        # is considerably faster due to using a hashtable instead of sorting
        # Once the indices of the true positive predictions are found in the smaller array containing only
        # predictions with IOU > min_iou, they are converted back into indices for the original array
        # using valid_pred.
        correct_preds = [valid_pred[0][unique_label_indices(best_gtruths[valid_pred[0]])]+num_total_detections for valid_pred in valid_preds]
        all_correct_preds.append(correct_preds)
        all_confs.append(confs)
        num_total_detections += num_detections
        num_total_gtruths += num_gtruths
    # Concatenates all predictions and confidences together to find class MAP
    all_confs = np.concatenate(all_confs)
    all_correct_preds = [np.concatenate(cur_pred) for cur_pred in zip(*all_correct_preds)]
    # Sets only correct prediction indices to true, rest to false.
    true_positives = np.zeros((len(min_ious), num_total_detections), dtype=bool)
    for iou_index, positive_locs in enumerate(all_correct_preds):
        true_positives[iou_index][positive_locs]=True
    # Mergesort is chosen to be consistent with coco/matlab results
    sort_order = all_confs.argsort(kind='mergesort')[::-1]
    true_positives = true_positives[:,sort_order]
    # Keeps track of number of true positives until each given point
    all_true_positives = np.cumsum(true_positives, axis=1)
    # PASCAL VOC 2012
    if avg_recalls is None:
        # Zero pad both sides to calculate area under curve
        precision = np.zeros((len(min_ious), num_total_detections+2), dtype=np.float64)
        # Pad one side with zeros and the other with ones for area under curve
        recall = np.zeros((len(min_ious), num_total_detections+2), dtype=np.float64)
        recall[:,-1] = np.ones(len(min_ious), dtype=np.float64)
        # In python >=3 this is equivalent to np.true_divide
        precision[:,1:-1] = all_true_positives / np.arange(1, num_total_detections+1)
        # Makes each element in precision list max of all elements to right (ignores endpoints)
        precision[:,1:-1] = np.maximum.accumulate(precision[:,-2:0:-1], axis=1)[:,::-1]
        recall[:,1:-1] = all_true_positives / num_total_gtruths
        # Calculate area under P-R curve for each IOU
        # Should only be one IOU at .5 for PASCAL
        all_areas = [] 
        for cur_recall, cur_precision in zip(recall, precision):
            # Find indices where value of recall changes
            change_points = np.nonzero(cur_recall[1:]!=cur_recall[:-1])[0]
            # Calculate sum of dw * dh as area and append to all areas
            all_areas.append(np.sum((cur_recall[change_points+1] - cur_recall[change_points]) * cur_precision[change_points+1]))
        return np.mean(all_areas)
    # PASCAL VOC 2007
    else:
        # The extra zero is to deal with a recall larger than is achieved by model
        precision = np.zeros((len(min_ious), num_total_detections+1), dtype=np.float64)
        # In python >=3 this is equivalent to np.true_divide
        precision[:,:-1] = all_true_positives / np.arange(1, num_total_detections+1)
        # Makes each element in precision list max of all elements to right (extra zero at right doesn't matter)
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
    files_in_ground_truth = set()
    with open(ground_truths, 'r') as truths_file:
        reader = csv.reader(truths_file)
        next(reader, None)
        if user_folders:
            for row in reader:
                all_boxes[row[CLASS_LOCATION]][(row[FOLDER_LOCATION], row[FILENAME_LOCATION])][0].append(row[PREDS_START:PREDS_END+1])
                files_in_ground_truth.add((row[FOLDER_LOCATION], row[FILENAME_LOCATION]))
        else:
            for row in reader:
                all_boxes[row[CLASS_LOCATION]][row[FILENAME_LOCATION]][0].append(row[PREDS_START:PREDS_END+1])
                files_in_ground_truth.add(row[FILENAME_LOCATION])
    with open(predictions, 'r') as preds_file:
        reader = csv.reader(preds_file)
        next(reader, None)
        if user_folders:
            for row in reader:
                if (row[FOLDER_LOCATION], row[FILENAME_LOCATION]) in files_in_ground_truth:
                    all_boxes[row[CLASS_LOCATION]][(row[FOLDER_LOCATION], row[FILENAME_LOCATION])][1].append(row[PREDS_START:PREDS_END+1]+row[BOX_CONFIDENCE_LOCATION:BOX_CONFIDENCE_LOCATION+1])
        else:
            for row in reader:
                if row[FILENAME_LOCATION] in files_in_ground_truth:
                    all_boxes[row[CLASS_LOCATION]][row[FILENAME_LOCATION]][1].append(row[PREDS_START:PREDS_END+1]+row[BOX_CONFIDENCE_LOCATION:BOX_CONFIDENCE_LOCATION+1])
    all_class_maps = {}
    for classname, all_file_preds in all_boxes.items():
        class_map = get_map_for_class(all_file_preds.values(), avg_recalls=None, min_ious=np.asarray([.5]))
        all_class_maps[classname] = class_map
    # Calculates average over all classes. This is the mAP for the test set.
    avg_map = sum(all_class_maps.values())/len(all_class_maps) if all_class_maps else 0 
    print('Class Name: Average, AP: {}'.format(avg_map))
    print('\n'.join('Class Name: {}, AP: {}'.format(*classdata) for classdata in all_class_maps.items()))
    with open(output, 'w') as out_file:
        csv_writer=csv.writer(out_file)
        csv_writer.writerow(['Class Name','AP'])
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

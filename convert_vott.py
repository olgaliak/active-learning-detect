import pandas as pd
import os
import json
import argparse
import config

def vis_all_detections_cv2(im, dets):

    classes  = dets['class'].tolist()
    scores   = dets['score'].tolist()
    bboxes_0 = dets['bbox_0'].tolist()
    bboxes_1 = dets['bbox_1'].tolist()
    bboxes_2 = dets['bbox_2'].tolist()
    bboxes_3 = dets['bbox_3'].tolist()
    im_widths = dets['im_width'].tolist()
    im_heights = dets['im_height'].tolist()
    filenames  = dets['image'].tolist()
    img_boxes = []
    for i in range(0, len(dets)):
        # Hadle images that did not have any detections
        if classes[i] == config.DetectConfig.CLASS_NA:
            continue

        box_dict = {}
        im_width = im_widths[i]
        im_height = im_heights[i]
        box_dict['x1'] = int(bboxes_1[i]*im_width)
        box_dict['y1'] = int(bboxes_0[i]*im_height)
        box_dict['x2'] = int(bboxes_3[i]*im_width)
        box_dict['y2'] = int(bboxes_2[i]*im_height)
        box_dict['id'] = i
        box_dict['width'] = im_width
        box_dict['height'] = im_height
        box_dict['type'] = 'Rectangle'
        box_dict['tags'] = [classes[i]]
        box_dict['name'] = i+1
        box_dict['fname'] = filenames[i]
        img_boxes.append(box_dict)
    
    return img_boxes


parser = argparse.ArgumentParser(description='convert object detection results to VOTT json')
parser.add_argument('--input', 
                    help='object detection log file')
parser.add_argument('--output', 
                    help='vott json file')
args = parser.parse_args()

# logfile = '/home/tinzha/Projects/Audi/object_detection/output-v2/audi_video_log.csv'
# raw_images = '/home/tinzha/Projects/Audi/object_detection/data-v2/raw'
# out_json_filename = 'big-person.json'
input_file = args.input
out_json_filename = args.output
dets = pd.read_csv(input_file, delimiter=',', header=0)
image_names = list(dets.image.unique())

#image_names = sorted(image_names, key =lambda x: int(x[-11:-5]))
#print (image_names)
# dets = log[log['score'] >= CONF_THRESH]
# image_names = [x for i,x in enumerate(list(dets.image.unique())) if x not in name_list_v1]


num = 0
id_num = 0
metadata = {}
name_list = sorted(image_names, key=lambda name: name.lower())
print (name_list)
for i in name_list:
    print (i)
    test = dets[dets['image'] == i]
    metadata[str(num)] = vis_all_detections_cv2(i, test)
    num = num+1

vott_meta = {}
vott_meta["frames"] = metadata
vott_meta["framerate"] = "1"
vott_meta["inputTags"] = "knot,defect"
vott_meta["suggestiontype"] = "track"
vott_meta["scd"] = 'false'
vott_meta["visitedFrames"] = list(range(len(image_names)))

with open(out_json_filename, 'w') as f:
    json.dump(vott_meta, f)
print("All done. Metadata is saved to {}". format(out_json_filename))

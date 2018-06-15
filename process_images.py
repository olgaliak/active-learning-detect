import collections
import pandas as pd
import os
import cv2
import json
import config
from datetime import datetime, timezone

def crop_objects(input_dir,
                   output_dir)                   :
    print("Starting processing, input {0}, output {1}".format(input_dir, output_dir))
    
    df = pd.read_csv(os.path.join(output_dir, config.config.DETS_FILE))
    images_data = df.groupby(["image"])
    cropped_dir_path = os.path.join(output_dir, config.config.CROPS_DIR)
    if not os.path.exists(cropped_dir_path):
        os.makedirs(cropped_dir_path)

    redacted_dir_path = os.path.join(output_dir, config.config.REDACTED_DIR)
    if not os.path.exists(redacted_dir_path):
        os.makedirs(redacted_dir_path)

    skipped_small = 0
    cropped_cnt = 0
    # Loop through all frames
    for image_data in images_data:
        image_fn = image_data[0]
        image_path = os.path.join(input_dir, image_fn)
        image_data_df = image_data[1]
        img_cv2 = cv2.imread(image_path)
        im_height, im_width = img_cv2.shape[0:2]

        fn_image, ext = os.path.splitext(os.path.basename(image_path))
        dict_image_data = {}
        dict_image_data["frame"] = fn_image;
        # Loop though all bboxes for the image

        for index, row in image_data_df.iterrows():
            if row["class"] != config.config.CROP_CLASS:
                continue
            ymin, xmin, ymax, xmax = row["bbox_0"], row["bbox_1"], row["bbox_2"], row["bbox_3"]
            # save crops and metadata
            # blurring
            (left, right, top, bottom) = (int(xmin * im_width), int(xmax * im_width),
                                      int(ymin * im_height), int(ymax * im_height))
            ic = img_cv2[top:bottom, left:right]
            ic_height, ic_width = ic.shape[0:2]

            if (ic_height < config.config.MIN_CROP_DIM) or (ic_width < config.config.MIN_CROP_DIM):
                skipped_small = skipped_small + 1
                continue

            crop_height = int(ic_height + 5)
            img_cropped = img_cv2[top:top + crop_height, left:right]
            img_cropped_fn = '{}_{}{}'.format(fn_image, index, ext)
            path_image_cropped = os.path.join(cropped_dir_path, img_cropped_fn)
            
            # save cropped image
            cv2.imwrite(path_image_cropped, img_cropped)
            cropped_cnt = cropped_cnt +1

    #     redacted_dir_path))
    print("Skipped {0} objects, height or width is less than {1}.".format(skipped_small, config.config.MIN_CROP_DIM))
    print("Created {0} crops.".format(cropped_cnt))
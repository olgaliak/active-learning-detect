import unittest
import shutil
import sys
import  os
import cv2
import numpy as np
from pathlib import Path
from collections import defaultdict
import filecmp
import six.moves.urllib as urllib



# Allow us to import files from "train'

train_dir = str(Path.cwd().parent / "train")
if train_dir not in sys.path:
    sys.path.append(train_dir)
from create_predictions import get_suggestions, make_csv_output
from tf_detector import TFDetector

class CreatePredictionsTestCase(unittest.TestCase):

    def setUp(self):
       url = "https://olgaliakrepo.blob.core.windows.net/woodknots/model_knots.pb"
       model_file = "model_knots.pb"
       if not os.path.exists(model_file):
           print("Downloading model: ", url)
           opener = urllib.request.URLopener()
           opener.retrieve(url, model_file)

    def tearDown(self):
        if os.path.exists("untagged.csv"):
            os.remove("untagged.csv")
        if os.path.exists("tagged_preds.csv"):
            os.remove("tagged_preds.csv")

    def test_make_csv_output(self):
        all_predictions = np.load('all_predictions.npy')
        basedir = Path("board_images_png")
        N_IMAGES = 4
        CV2_COLOR_LOAD_FLAG = 1
        all_image_files = list(basedir.rglob("*.png"))[0:N_IMAGES]
        all_names = []
        all_names += [("board_images_png", filename.name) for filename in all_image_files ]

        all_sizes = [cv2.imread(str(image), CV2_COLOR_LOAD_FLAG).shape[:2] for image in all_image_files]
        untagged_output = 'untagged.csv'
        tagged_output = 'tagged_preds.csv'
        already_tagged = defaultdict(set)
        make_csv_output(all_predictions, all_names, all_sizes, untagged_output, tagged_output, already_tagged,
                        user_folders = True)

        self.assertEqual(filecmp.cmp('untagged.csv', 'untagged_source.csv'), True, "generated untagged.csv is correct")

    def test_get_suggestions(self):
        classes = 'knot,defect'
        cur_detector = TFDetector(classes.split(','), 'model_knots.pb')
        image_dir = "test_workdir_train"
        untagged_output = 'untagged.csv'
        tagged_output = 'tagged_preds.csv'
        cur_tagged = None
        cur_tagging = None
        get_suggestions(cur_detector, image_dir, untagged_output, tagged_output, cur_tagged, cur_tagging,
                        filetype="*.png", min_confidence=0.5,
                        user_folders=True)
        self.assertEqual(filecmp.cmp('untagged.csv', 'untagged_source.csv'), True, "generated untagged.csv is correct")


if __name__ == '__main__':
    unittest.main()

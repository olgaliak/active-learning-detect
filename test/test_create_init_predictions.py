import unittest
import shutil
import sys
import  os
import cv2
import numpy as np
from pathlib import Path
from collections import defaultdict
import filecmp



# Allow us to import files from "train'

train_dir = str(Path.cwd().parent / "train")
if train_dir not in sys.path:
    sys.path.append(train_dir)
from create_predictions import get_suggestions, make_csv_output
from tf_detector import TFDetector
import six.moves.urllib as urllib
import tarfile
TEST_WORKDIR = "test_workdir"

class CreateInitPredictionsTestCase(unittest.TestCase):
    def setUp(self):
        DOWNLOAD_BASE = 'http://download.tensorflow.org/models/object_detection/'
        MODEL_NAME = 'faster_rcnn_resnet101_coco_2018_01_28'  # 'ssd_mobilenet_v1_coco_2017_11_17'
        MODEL_FILE = MODEL_NAME + '.tar.gz'
        url = DOWNLOAD_BASE + MODEL_FILE
        MODEL_FILE_DST = os.path.join(TEST_WORKDIR, MODEL_FILE)
        self.froz_graph = os.path.join(TEST_WORKDIR, MODEL_NAME, "frozen_inference_graph.pb")
        if not os.path.exists(self.froz_graph):
            if not os.path.exists(MODEL_FILE_DST):
                print("Downloading model: ", url)
                opener = urllib.request.URLopener()
                opener.retrieve(url, MODEL_FILE_DST)
            print("Unzipping: ", MODEL_FILE_DST)
            tar_file = tarfile.open(MODEL_FILE_DST)
            for file in tar_file.getmembers():
                file_name = os.path.basename(file.name)
                if 'frozen_inference_graph.pb' in file_name:
                    tar_file.extract(file, TEST_WORKDIR)

    def tearDown(self):
        if os.path.exists("untagged.csv"):
            os.remove("untagged.csv")
        if os.path.exists("tagged_preds.csv"):
            os.remove("tagged_preds.csv")
        #print("TBD tear down")

    def test_make_csv_output(self):
        all_predictions = np.load('all_predictions_cow.npy')
        basedir = Path("camera_images")

        CV2_COLOR_LOAD_FLAG = 1
        all_image_files = list(basedir.rglob("*.JPG"))
        all_names = []
        all_names += [("camera_images", filename.name) for filename in all_image_files ]

        all_sizes = [cv2.imread(str(image), CV2_COLOR_LOAD_FLAG).shape[:2] for image in all_image_files]
        untagged_output = 'untagged.csv'
        tagged_output = 'tagged_preds.csv'
        already_tagged = defaultdict(set)
        make_csv_output(all_predictions, all_names, all_sizes, untagged_output, tagged_output, already_tagged,
                        user_folders = True)

        self.assertEqual(filecmp.cmp('untagged.csv', 'untagged_cow.csv'), True, "generated untagged.csv is correct")


    def test_get_suggestions(self):
        classesIDs = list(range(1, 91))
        classes = [str(x) for x in classesIDs]
        cur_detector = TFDetector(classes, self.froz_graph)
        image_dir = "test_workdir_init_pred"
        untagged_output = 'untagged.csv'
        tagged_output = 'tagged_preds.csv'
        cur_tagged = None
        cur_tagging = None
        get_suggestions(cur_detector, image_dir, untagged_output, tagged_output, cur_tagged, cur_tagging,
                        filetype="*.jpg", min_confidence=0.5,
                        user_folders=True)
        self.assertEqual(filecmp.cmp('untagged.csv', 'untagged_cow.csv'), True, "generated untagged.csv is correct")


if __name__ == '__main__':
    unittest.main()

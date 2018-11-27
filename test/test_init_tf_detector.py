import unittest
import shutil
import sys
import  os
import numpy as np
import cv2
from pathlib import Path
import six.moves.urllib as urllib
import tarfile


# Allow us to import utils
config_dir = str(Path.cwd().parent / "utils")
if config_dir not in sys.path:
    sys.path.append(config_dir)
from config import Config

train_dir = str(Path.cwd().parent / "train")
if train_dir not in sys.path:
    sys.path.append(train_dir)
from tf_detector import TFDetector

TEST_WORKDIR = "test_workdir"

class TFDetectorTestCase(unittest.TestCase):
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
        #shutil.rmtree(self.tagging_location, ignore_errors=True)
        print("Tear down")

    def test_predict(self):
        classesIDs = list(range(1,91))
        classes = ','.join(str(x) for x in classesIDs )
        detector = TFDetector(classes.split(','),self.froz_graph)
        basedir = Path("camera_images")

        all_image_files = list(basedir.rglob("*.JPG"))
        image_size = (1000,750)
        NUM_CHANNELS = 3
        CV2_COLOR_LOAD_FLAG = 1
        all_images = np.zeros((len(all_image_files), *reversed(image_size), NUM_CHANNELS), dtype=np.uint8)
        for curindex, image in enumerate(all_image_files):
            all_images[curindex] = cv2.resize(cv2.imread(str(image), CV2_COLOR_LOAD_FLAG), image_size)
        all_predictions = detector.predict(all_images, min_confidence=0.5)

        self.assertEqual(len(all_predictions), len(all_image_files))

        expected_allpred = np.load('all_predictions_cow.npy')

        self.assertEqual((all_predictions == expected_allpred).all(), True,
                         "(expected_allpred == all_predictions).all()")

        #np.save('all_predictions_cow', all_predictions)



if __name__ == '__main__':
    unittest.main()

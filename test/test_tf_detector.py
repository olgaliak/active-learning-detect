import unittest
import shutil
import sys
import  os
import numpy as np
import cv2
from pathlib import Path
import six.moves.urllib as urllib


# Allow us to import utils
config_dir = str(Path.cwd().parent / "utils")
if config_dir not in sys.path:
    sys.path.append(config_dir)
from config import Config

train_dir = str(Path.cwd().parent / "train")
if train_dir not in sys.path:
    sys.path.append(train_dir)
from tf_detector import TFDetector

class TFDetectorTestCase(unittest.TestCase):
    def setUp(self):
        url = "https://olgaliakrepo.blob.core.windows.net/woodknots/model_knots.pb"
        model_file = "model_knots.pb"
        if not os.path.exists(model_file):
            print("Downloading model: ", url)
            opener = urllib.request.URLopener()
            opener.retrieve(url, model_file)

    def tearDown(self):
        #shutil.rmtree(self.tagging_location, ignore_errors=True)
        print("Tear down")

    def test_predict(self):
        classes = 'knot,defect'
        detector = TFDetector(classes.split(','),'model_knots.pb')

        basedir = Path("board_images_png")
        N_IMAGES = 4
        all_image_files = list(basedir.rglob("*.png"))[0:N_IMAGES]
        image_size = (1000,750)
        NUM_CHANNELS = 3
        CV2_COLOR_LOAD_FLAG = 1
        all_images = np.zeros((len(all_image_files), *reversed(image_size), NUM_CHANNELS), dtype=np.uint8)
        for curindex, image in enumerate(all_image_files):
            all_images[curindex] = cv2.resize(cv2.imread(str(image), CV2_COLOR_LOAD_FLAG), image_size)
        all_predictions = detector.predict(all_images, min_confidence=0.5)

        self.assertEqual(len(all_predictions), N_IMAGES)

        expected_allpred = np.load('all_predictions.npy')
        self.assertEqual((all_predictions == expected_allpred).all(), True, "(expected_allpred == all_predictions).all()")


if __name__ == '__main__':
    unittest.main()

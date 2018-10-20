import unittest
import shutil
import sys
import  os
from pathlib import Path

# Allow us to import utils
config_dir = str(Path.cwd().parent / "utils")
if config_dir not in sys.path:
    sys.path.append(config_dir)
from config import Config

tag_dir = str(Path.cwd().parent / "tag")
if tag_dir not in sys.path:
    sys.path.append(tag_dir)
from download_vott_json import create_vott_json, get_top_rows


class DownloadVOTTJSONTestCase(unittest.TestCase):
    def setUp(self):
        self.config_file = Config.parse_file("../workconfig.ini")

        self.tagging_location = self.config_file["tagging_location"] + "_test"
        shutil.rmtree(self.tagging_location, ignore_errors=True)
        self.csv_file_loc = Path(self.config_file["tagging_location"])
        # prepare file
        shutil.copyfile("./totag_source.csv", str(self.csv_file_loc / "totag.csv"))

        self.csv_file_loc.mkdir(parents=True, exist_ok=True)
        self.ideal_class_balance = self.config_file["ideal_class_balance"].split(",")
        self. max_tags_per_pixel = self.config_file.get("max_tags_per_pixel")
        self.tag_names = self.config_file["classes"].split(",")
        self.user_folders = self.config_file["user_folders"] == "True"
        self.pick_max  = self.config_file["pick_max"] == "True"

    def tearDown(self):
        #shutil.rmtree(self.tagging_location, ignore_errors=True)
        print("Tear down")

    def test_get_top_rows(self):
        N_ROWS = 3
        N_FILES = 3
        EXPECTED = [[['st1840.png', 'knot', '0.12036637', '0.18497443', '0.7618415', '0.8283344', '512', '488', 'board_images_png', '0.986', '0.986'],
                     ['st1840.png', 'knot', '0.7297609', '0.7755673', '0.62443626', '0.6670296', '512', '488', 'board_images_png', '0.986', '0.986'],
                     ['st1840.png', 'defect', '0.76513', '0.9952971', '0.6075407', '0.6546806', '512', '488', 'board_images_png', '0.986', '0.986']],
                    [['st1578.png', 'knot', '0.594302', '0.6663906', '0.35276932', '0.43525606', '512', '488', 'board_images_png', '0.98448783', '0.98448783']],
                    [['st1026.png', 'knot', '0.2674017', '0.35383838', '0.39859554', '0.50976944', '512', '488', 'board_images_png', '0.9884343', '0.96366304'],
                     ['st1026.png', 'knot', '0.69417506', '0.744075', '0.34379873', '0.39051458', '512', '488', 'board_images_png', '0.97863936', '0.96366304'],
                     ['st1026.png', 'defect', '0.70078284', '0.9907891', '0.5857268', '0.6470487', '512', '488', 'board_images_png', '0.96366304', '0.96366304']]]

        all_rows = get_top_rows(self.csv_file_loc, N_ROWS, self.user_folders ,
                         self.pick_max, self.tag_names, self.ideal_class_balance)
        self.assertEqual(len(all_rows), N_FILES, 'number of rows')
        self.assertEqual(all_rows, EXPECTED, 'row values')

    def test_create_vott_json(self):
        N_ROWS = 3
        N_FILES = 3
        FOLDER_NAME = "board_images_png"
        create_vott_json(self.csv_file_loc,  N_ROWS,  self.user_folders ,
                         self.pick_max, "",
                         self.tagging_location, blob_credentials=None,
                         tag_names= self.tag_names,
                         max_tags_per_pixel=self. max_tags_per_pixel ,
                         ideal_class_balance=self.ideal_class_balance)

        res_folder = os.path.join(self.tagging_location, FOLDER_NAME)
        res_immages_cnt = sum([len(files) for r, d, files in os.walk(res_folder)])
        self.assertEqual(N_FILES, res_immages_cnt)


if __name__ == '__main__':
    unittest.main()

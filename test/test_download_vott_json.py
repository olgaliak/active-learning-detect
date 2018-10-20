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
        all_files = get_top_rows(self.csv_file_loc, N_ROWS, self.user_folders ,
                         self.pick_max, self.tag_names, self.ideal_class_balance)
        self.assertEqual(len(all_files), N_FILES)

    def test_create_vott_json(self):
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

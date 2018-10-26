import unittest
import shutil
import sys
import  os
from pathlib import Path
import filecmp

# Allow us to import utils
config_dir = str(Path.cwd().parent / "utils")
if config_dir not in sys.path:
    sys.path.append(config_dir)
from config import Config

tag_dir = str(Path.cwd().parent / "tag")
if tag_dir not in sys.path:
    sys.path.append(tag_dir)
from download_vott_json import create_vott_json, get_top_rows


class DownloadInitVOTTJSONTestCase(unittest.TestCase):
    def setUp(self):
        self.config_file = Config.parse_file("../workconfig.ini")

        self.tagging_location = self.config_file["tagging_location"] + "_test"
        shutil.rmtree(self.tagging_location, ignore_errors=True)
        self.csv_file_loc = Path(self.config_file["tagging_location"])

        self.csv_file_loc.mkdir(parents=True, exist_ok=True)
        self. max_tags_per_pixel = self.config_file.get("max_tags_per_pixel")
        self.tag_names = self.config_file["classes"].split(",")
        self.user_folders = self.config_file["user_folders"] == "True"
        self.pick_max  = self.config_file["pick_max"] == "True"



    def tearDown(self):
        # shutil.rmtree(self.tagging_location, ignore_errors=True)
        # shutil.rmtree("Images", ignore_errors=True)
        #
        # if os.path.exists("totag.csv"):
        #     os.remove("totag.csv")
        #
        # if os.path.exists("tagging.csv"):
        #         os.remove("tagging.csv")
        # if os.path.exists("Images.json"):
        #     os.remove("Images.json")

        print("Tear down")

    def test_create_vott_json(self):
        # prepare file
        shutil.copyfile("./untagged_cow.csv", "totag.csv")

        csv_file_loc = Path('.')
        FOLDER = "camera_images"
        N_IMAGES = sum([len(files) for r, d, files in os.walk(FOLDER)])
        user_folders = False
        pick_max = True
        tagging_location = "."
        classesIDs = list(range(1, 91))
        classes = ','.join(str(x) for x in classesIDs)
        create_vott_json(csv_file_loc, N_IMAGES, user_folders,
                         pick_max, FOLDER,
                         tagging_location, blob_credentials = None,
                         tag_names= classes.split(','),
                         max_tags_per_pixel= 2,
                         config_class_balance=None
                         )
        #self.assertEqual(filecmp.cmp('Images.json', 'Images_source.json'), True, "generated VOTT json is correct")

if __name__ == '__main__':
    unittest.main()

import unittest
import shutil
import sys
import  os
from pathlib import Path
import filecmp
import json
import numpy as np

# Allow us to import utils
config_dir = str(Path.cwd().parent / "utils")
if config_dir not in sys.path:
    sys.path.append(config_dir)
from config import Config

tag_dir = str(Path.cwd().parent / "tag")
if tag_dir not in sys.path:
    sys.path.append(tag_dir)
from download_vott_json import create_init_vott_json, create_vott_json, get_top_rows, filter_top, add_bkg_class_name, remove_bkg_class_name, parse_class_balance_setting


class DownloadInitVOTTJSONTestCase(unittest.TestCase):
    def setUp(self):
        self.config_file = Config.parse_file("testconfig.ini")

        self.tagging_location = self.config_file["tagging_location"] + "_test"
        shutil.rmtree(self.tagging_location, ignore_errors=True)
        self.csv_file_loc = Path(self.config_file["tagging_location"])

        self.csv_file_loc.mkdir(parents=True, exist_ok=True)
        self. max_tags_per_pixel = self.config_file.get("max_tags_per_pixel")
        self.tag_names = self.config_file["classes"].split(",")
        self.user_folders = self.config_file["user_folders"] == "True"
        self.pick_max  = self.config_file["pick_max"] == "True"



    def tearDown(self):
        shutil.rmtree(self.tagging_location, ignore_errors=True)
        shutil.rmtree("Images", ignore_errors=True)

        shutil.rmtree("test_workdir/camera_images", ignore_errors=True)
        shutil.rmtree("test_workdir90", ignore_errors=True)
        if os.path.exists(r"test_workdir/camera_images.json"):
            os.remove(r"test_workdir/camera_images.json")

        if os.path.exists("totag.csv"):
            os.remove("totag.csv")

        if os.path.exists("tagging.csv"):
                os.remove("tagging.csv")
        if os.path.exists("Images.json"):
            os.remove("Images.json")

        if os.path.exists("init_totag.csv"):
            os.remove("init_totag.csv")

        print("Tear down")


    def test_create_vott_json_90(self):
        # prepare file
        shutil.copyfile("./untagged_cow.csv", "totag.csv")

        csv_file_loc = Path('.')
        FOLDER = "camera_images"
        N_IMAGES = sum([len(files) for r, d, files in os.walk(FOLDER)])
        user_folders = False
        pick_max = True
        tagging_location = "."
        tagging_location = "test_workdir90"
        classesIDs =  [str(i) for i in (range(1, 91))]
        tag_names = add_bkg_class_name(classesIDs)

        ideal_class_balance = parse_class_balance_setting(None, len(tag_names))
        create_vott_json(csv_file_loc, N_IMAGES, user_folders,
                         pick_max, FOLDER,
                         tagging_location, blob_credentials = None,
                         tag_names= tag_names,
                         max_tags_per_pixel= 2,
                         config_class_balance=ideal_class_balance
                         )



        self.assertEqual(filecmp.cmp(os.path.join(tagging_location, 'Images.json'), 'Images_source_workdir90.json'), True, "generated VOTT json is correct")

    def test_get_filtered(self):
        shutil.copyfile("./untagged_cow.csv", "init_totag.csv")
        json_fn = "init_classes_map.json"
        json_config = None
        with open(json_fn, "r") as read_file:
            json_config = json.load(read_file)
        classmap = json_config["classmap"]
        ideal_balance_list = []
        new_tag_names = []
        init_tag_names = []
        class_map_dict = {}
        for m in classmap:
            ideal_balance_list.append(m['balance'])
            new_tag_names.append(m['map'])
            init_tag_names.append(m['initclass'])
            class_map_dict[m['initclass']] = m['map']
        ideal_balance = ','.join(ideal_balance_list)
        unmapclass_list = json_config["unmapclass"]
        default_class = json_config["default_class"]
        file_location_totag = Path('.')/"init_totag.csv"
        new_tag_names = add_bkg_class_name(new_tag_names)
        ideal_class_balance = parse_class_balance_setting(ideal_balance, len(new_tag_names))

        rows, _, _ = get_top_rows(file_location_totag, 10,  True,  False,
                             init_tag_names,  ideal_class_balance,
                            filter_top,
                            unmapclass_list, init_tag_names, class_map_dict, default_class)

        expected_rows = np.load("init_class_get_rows_min.npy")
        self.assertEqual((rows == expected_rows).all(), True)
        print("")

    def test_create_vott_json(self):
        # prepare file
        shutil.copyfile("./untagged_cow.csv", "init_totag.csv")

        csv_file_loc = Path('.')
        FOLDER = "camera_images"
        N_IMAGES =  10
        user_folders = True
        pick_max = False
        tagging_location = "test_workdir"

        json_fn = "init_classes_map.json"
        json_config = None
        with open(json_fn, "r") as read_file:
            json_config = json.load(read_file)
        classmap = json_config["classmap"]
        ideal_balance_list = []
        new_tag_names = []
        init_tag_names = []
        class_map_dict = {}
        for m in classmap:
            ideal_balance_list.append(m['balance'])
            new_tag_names.append(m['map'])
            init_tag_names.append(m['initclass'])
            class_map_dict[m['initclass']] = m['map']

        unmapclass_list = json_config["unmapclass"]
        default_class = json_config["default_class"]
        ideal_balance = ','.join(ideal_balance_list)
        new_tag_names.append(default_class)
        new_tag_names = remove_bkg_class_name(new_tag_names)
        ideal_class_balance = parse_class_balance_setting(ideal_balance, len(init_tag_names))

        create_init_vott_json(csv_file_loc , N_IMAGES, user_folders,
                         pick_max,
                         "", #image loc
                         tagging_location,
                         None, #blob creds
                         init_tag_names,
                         new_tag_names,
                         2, #max pix
                         ideal_class_balance,
                         ["#e9f1fe", "#33BBFF", "#FFFF19"], #colors
                         unmapclass_list, init_tag_names, class_map_dict, default_class )

        self.assertEqual(filecmp.cmp(os.path.join( tagging_location, FOLDER +'.json'),   FOLDER + '_source.json'), True, "generated VOTT json is correct")

if __name__ == '__main__':
    unittest.main()

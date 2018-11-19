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
from download_vott_json import create_vott_json, get_top_rows, add_bkg_class_name, parse_class_balance_setting, make_vott_output


class DownloadVOTTJSONTestCase(unittest.TestCase):
    def setUp(self):
        self.config_file = Config.parse_file("testconfig.ini")

        self.tagging_location = self.config_file["tagging_location"] + "_test"
        shutil.rmtree(self.tagging_location, ignore_errors=True)
        self.totag_csv_file_loc = Path(self.config_file["tagging_location"])/"totag.csv"

        Path(self.config_file["tagging_location"]).mkdir(parents=True, exist_ok=True)
        self. max_tags_per_pixel = self.config_file.get("max_tags_per_pixel")
        self.tag_names = self.config_file["classes"].split(",")
        self.user_folders = self.config_file["user_folders"] == "True"
        self.pick_max  = self.config_file["pick_max"] == "True"



    def tearDown(self):
        shutil.rmtree(self.tagging_location, ignore_errors=True)
        shutil.rmtree("Images", ignore_errors=True)

        if os.path.exists("totag.csv"):
            os.remove("totag.csv")

        if os.path.exists("tagging.csv"):
                os.remove("tagging.csv")
        if os.path.exists("Images.json"):
            os.remove("Images.json")

        print("Tear down")

    def test_get_top_rows(self):
        # prepare file
        shutil.copyfile("./totag_source.csv", str(self.totag_csv_file_loc))

        N_ROWS = 3
        N_FILES = 3
        EXPECTED = [[['st1840.png', 'knot', '0.12036637', '0.18497443', '0.7618415', '0.8283344', '512', '488', 'board_images_png', '0.986', '0.986'],
                     ['st1840.png', 'knot', '0.7297609', '0.7755673', '0.62443626', '0.6670296', '512', '488', 'board_images_png', '0.986', '0.986'],
                     ['st1840.png', 'defect', '0.76513', '0.9952971', '0.6075407', '0.6546806', '512', '488', 'board_images_png', '0.986', '0.986']],
                    [['st1578.png', 'knot', '0.594302', '0.6663906', '0.35276932', '0.43525606', '512', '488', 'board_images_png', '0.98448783', '0.98448783']],
                    [['st1026.png', 'knot', '0.2674017', '0.35383838', '0.39859554', '0.50976944', '512', '488', 'board_images_png', '0.9884343', '0.96366304'],
                     ['st1026.png', 'knot', '0.69417506', '0.744075', '0.34379873', '0.39051458', '512', '488', 'board_images_png', '0.97863936', '0.96366304'],
                     ['st1026.png', 'defect', '0.70078284', '0.9907891', '0.5857268', '0.6470487', '512', '488', 'board_images_png', '0.96366304', '0.96366304']]]

        class_balance = "0.7,0.3,0"

        tag_names = add_bkg_class_name(self.tag_names)
        ideal_class_balance = parse_class_balance_setting(class_balance, len(tag_names))

        all_rows, _, _ = get_top_rows(self.totag_csv_file_loc, N_ROWS, self.user_folders,
                                      self.pick_max, tag_names, ideal_class_balance)
        self.assertEqual(len(all_rows), N_FILES, 'number of rows')
        self.assertEqual(all_rows, EXPECTED, 'raw values')

    def test_get_top_rows_no_folder(self):
        # prepare file
        shutil.copyfile("./totag_no_folder_source.csv", str(self.totag_csv_file_loc))

        N_ROWS = 3
        N_FILES = 3
        EXPECTED = [[['st1840.png', 'knot', '0.12036637', '0.18497443', '0.7618415', '0.8283344', '512', '488',
                       '0.986', '0.986'],
                     ['st1840.png', 'knot', '0.7297609', '0.7755673', '0.62443626', '0.6670296', '512', '488',
                       '0.986', '0.986'],
                     ['st1840.png', 'defect', '0.76513', '0.9952971', '0.6075407', '0.6546806', '512', '488',
                       '0.986', '0.986']],
                    [['st1578.png', 'knot', '0.594302', '0.6663906', '0.35276932', '0.43525606', '512', '488',
                       '0.98448783', '0.98448783']],
                    [['st1026.png', 'knot', '0.2674017', '0.35383838', '0.39859554', '0.50976944', '512', '488',
                       '0.9884343', '0.96366304'],
                     ['st1026.png', 'knot', '0.69417506', '0.744075', '0.34379873', '0.39051458', '512', '488',
                      '0.97863936', '0.96366304'],
                     ['st1026.png', 'defect', '0.70078284', '0.9907891', '0.5857268', '0.6470487', '512', '488',
                       '0.96366304', '0.96366304']]]

        class_balance = "0.7,0.3,0"
        user_folders = False

        tag_names = add_bkg_class_name(self.tag_names)
        ideal_class_balance = parse_class_balance_setting(class_balance, len(tag_names))

        all_rows, _, _ = get_top_rows(self.totag_csv_file_loc, N_ROWS, user_folders,
                                      self.pick_max, tag_names, ideal_class_balance)
        self.assertEqual(len(all_rows), N_FILES, 'number of rows')
        self.assertEqual(all_rows, EXPECTED, 'raw values')

    def test_get_top_rows_empty_class_balance(self):
        # prepare file
        shutil.copyfile("./totag_source.csv", str(self.totag_csv_file_loc))

        N_ROWS = 3
        N_FILES = 3
        EXPECTED = [[['st1840.png', 'knot', '0.12036637', '0.18497443', '0.7618415', '0.8283344', '512', '488', 'board_images_png', '0.986', '0.986'],
                     ['st1840.png', 'knot', '0.7297609', '0.7755673', '0.62443626', '0.6670296', '512', '488', 'board_images_png', '0.986', '0.986'],
                     ['st1840.png', 'defect', '0.76513', '0.9952971', '0.6075407', '0.6546806', '512', '488', 'board_images_png', '0.986', '0.986']],
                     [['st1578.png', 'knot', '0.594302', '0.6663906', '0.35276932', '0.43525606', '512', '488', 'board_images_png', '0.98448783', '0.98448783']],
                     [['st1611.png', 'knot', '0.6326234', '0.7054164', '0.86741334', '0.96444726', '512', '488', 'board_images_png', '0.99616516', '0.9843567'],
                      ['st1611.png', 'knot', '0.07399843', '0.11282173', '0.32572043', '0.36819047', '512', '488', 'board_images_png', '0.9843567', '0.9843567']]]
        class_balance = ''
        tag_names = add_bkg_class_name(self.tag_names)
        ideal_class_balance = parse_class_balance_setting(class_balance, len(tag_names))
        all_rows, _, _ = get_top_rows(self.totag_csv_file_loc, N_ROWS, self.user_folders,
                                      self.pick_max, tag_names, ideal_class_balance)
        self.assertEqual(len(all_rows), N_FILES, 'number of rows')
        self.assertEqual(all_rows, EXPECTED, 'raw values')

    def test_get_top_rows_invalid_class_balance1(self):
        # prepare file
        shutil.copyfile("./totag_source.csv", str(self.totag_csv_file_loc))

        N_ROWS = 3
        N_FILES = 3
        EXPECTED = [[['st1840.png', 'knot', '0.12036637', '0.18497443', '0.7618415', '0.8283344', '512', '488', 'board_images_png', '0.986', '0.986'],
                     ['st1840.png', 'knot', '0.7297609', '0.7755673', '0.62443626', '0.6670296', '512', '488', 'board_images_png', '0.986', '0.986'],
                     ['st1840.png', 'defect', '0.76513', '0.9952971', '0.6075407', '0.6546806', '512', '488', 'board_images_png', '0.986', '0.986']],
                     [['st1578.png', 'knot', '0.594302', '0.6663906', '0.35276932', '0.43525606', '512', '488', 'board_images_png', '0.98448783', '0.98448783']],
                     [['st1611.png', 'knot', '0.6326234', '0.7054164', '0.86741334', '0.96444726', '512', '488', 'board_images_png', '0.99616516', '0.9843567'],
                      ['st1611.png', 'knot', '0.07399843', '0.11282173', '0.32572043', '0.36819047', '512', '488', 'board_images_png', '0.9843567', '0.9843567']]]
        class_balance = 'Random'
        tag_names = add_bkg_class_name(self.tag_names)
        ideal_class_balance = parse_class_balance_setting(class_balance, len(tag_names))

        all_rows, _, _ = get_top_rows(self.totag_csv_file_loc, N_ROWS, self.user_folders,
                                      self.pick_max, tag_names, ideal_class_balance)
        self.assertEqual(len(all_rows), N_FILES, 'number of rows')
        self.assertEqual(all_rows, EXPECTED, 'raw values')

    def test_get_top_rows_invalid_class_balance2(self):
        # prepare file
        shutil.copyfile("./totag_source.csv", str(self.totag_csv_file_loc))

        N_ROWS = 3
        N_FILES = 3
        EXPECTED = [[['st1840.png', 'knot', '0.12036637', '0.18497443', '0.7618415', '0.8283344', '512', '488', 'board_images_png', '0.986', '0.986'],
                     ['st1840.png', 'knot', '0.7297609', '0.7755673', '0.62443626', '0.6670296', '512', '488', 'board_images_png', '0.986', '0.986'],
                     ['st1840.png', 'defect', '0.76513', '0.9952971', '0.6075407', '0.6546806', '512', '488', 'board_images_png', '0.986', '0.986']],
                     [['st1578.png', 'knot', '0.594302', '0.6663906', '0.35276932', '0.43525606', '512', '488', 'board_images_png', '0.98448783', '0.98448783']],
                     [['st1611.png', 'knot', '0.6326234', '0.7054164', '0.86741334', '0.96444726', '512', '488', 'board_images_png', '0.99616516', '0.9843567'],
                      ['st1611.png', 'knot', '0.07399843', '0.11282173', '0.32572043', '0.36819047', '512', '488', 'board_images_png', '0.9843567', '0.9843567']]]

        class_balance = '0.1, 0.2, 0.3'
        tag_names = add_bkg_class_name(self.tag_names)
        ideal_class_balance = parse_class_balance_setting(class_balance, len(tag_names))
        all_rows, _, _ = get_top_rows(self.totag_csv_file_loc, N_ROWS, self.user_folders,
                                      self.pick_max, tag_names, ideal_class_balance)
        self.assertEqual(len(all_rows), N_FILES, 'number of rows')
        self.assertEqual(all_rows, EXPECTED, 'raw values')

    def test_get_top_rows_class_balance_min(self):
        # prepare file
        shutil.copyfile("./totag_source.csv", str(self.totag_csv_file_loc))

        N_ROWS = 3
        EXPECTED = [[['st1091.png', 'knot', '0.20989896', '0.251748', '0.34986168', '0.3921352', '512', '488', 'board_images_png', '0.99201256', '0.70161'],
                                     ['st1091.png', 'knot', '0.696119', '0.7461088', '0.27078417', '0.33086362', '512', '488', 'board_images_png', '0.9827361', '0.70161'],
                                     ['st1091.png', 'knot', '0.89531857', '0.93743694', '0.4605299', '0.5066802', '512', '488', 'board_images_png', '0.9794672', '0.70161'],
                                     ['st1091.png', 'defect', '0.7629506', '1.0', '0.6205898', '0.67307687', '512', '488', 'board_images_png', '0.74762243', '0.70161'],
                                     ['st1091.png', 'knot', '0.14214082', '0.247842', '0.7355515', '0.8967391', '512', '488', 'board_images_png', '0.7072498', '0.70161'],
                                     ['st1091.png', 'defect', '0.0', '0.1281265', '0.55038965', '0.59755194', '512', '488', 'board_images_png', '0.70161', '0.70161']],
                                    [['st1185.png', 'knot', '0.6978268', '0.7582275', '0.66821593', '0.7535644', '512', '488', 'board_images_png', '0.97257924', '0.7035888'],
                                     ['st1185.png', 'defect', '0.35780182', '0.60781866', '0.27580062', '0.32093963', '512', '488', 'board_images_png', '0.9720861', '0.7035888'],
                                     ['st1185.png', 'knot', '0.5183983', '0.57071316', '0.84764653', '0.91617334', '512', '488', 'board_images_png', '0.9241496', '0.7035888'],
                                     ['st1185.png', 'knot', '0.55567926', '0.5904746', '0.51832056', '0.5461106', '512', '488', 'board_images_png', '0.7035888', '0.7035888']],
                                    [['st1192.png', 'knot', '0.39846605', '0.45543727', '0.36765742', '0.4488806', '512', '488', 'board_images_png', '0.99612194', '0.7127546'],
                                     ['st1192.png', 'defect', '0.07790943', '0.44866413', '0.5975798', '0.640683', '512', '488', 'board_images_png', '0.80447847', '0.7127546'],
                                     ['st1192.png', 'defect', '0.47953823', '0.7499259', '0.5517361', '0.59940904', '512', '488', 'board_images_png', '0.7127546', '0.7127546']]]

        pick_max = False
        class_balance = "0.7,0.3,0"
        tag_names = add_bkg_class_name(self.tag_names)
        ideal_class_balance = parse_class_balance_setting(class_balance, len(tag_names))
        all_rows, _, _ = get_top_rows(self.totag_csv_file_loc, N_ROWS, self.user_folders,
                                      pick_max, tag_names, ideal_class_balance)
        #self.assertEqual(len(all_rows), N_FILES, 'number of rows')
        self.assertEqual(all_rows, EXPECTED, 'raw values')

    def test_create_vott_json(self):
        # prepare file
        shutil.copyfile("./totag_source.csv", "./totag.csv")

        N_ROWS = 3
        N_FILES = 3
        FOLDER_NAME = "board_images_png"
        class_balance = "0.7,0.3,0"
        tag_names = add_bkg_class_name(self.tag_names)
        ideal_class_balance = parse_class_balance_setting(class_balance, len(tag_names))

        create_vott_json(self.totag_csv_file_loc, N_ROWS, self.user_folders,
                         self.pick_max, "",
                         self.tagging_location, blob_credentials=None,
                         tag_names= tag_names,
                         max_tags_per_pixel=self. max_tags_per_pixel,
                         config_class_balance= ideal_class_balance)

        res_folder = os.path.join(self.tagging_location, FOLDER_NAME)
        res_immages_cnt = sum([len(files) for r, d, files in os.walk(res_folder)])
        self.assertEqual(N_FILES, res_immages_cnt)

    def test_get_top_rows_with_bkg(self):
        # prepare file
        shutil.copyfile("./totag_source.csv", str(self.totag_csv_file_loc))

        N_ROWS = 5
        N_FILES = 5
        EXPECTED = [[['st1840.png', 'knot', '0.12036637', '0.18497443', '0.7618415', '0.8283344', '512', '488', 'board_images_png', '0.986', '0.986'],
                     ['st1840.png', 'knot', '0.7297609', '0.7755673', '0.62443626', '0.6670296', '512', '488', 'board_images_png', '0.986', '0.986'],
                     ['st1840.png', 'defect', '0.76513', '0.9952971', '0.6075407', '0.6546806', '512', '488', 'board_images_png', '0.986', '0.986']],
                    [['st1578.png', 'knot', '0.594302', '0.6663906', '0.35276932', '0.43525606', '512', '488', 'board_images_png', '0.98448783', '0.98448783']],
                    [['st1611.png', 'knot', '0.6326234', '0.7054164', '0.86741334', '0.96444726', '512', '488',
                      'board_images_png', '0.99616516', '0.9843567'],
                     ['st1611.png', 'knot', '0.07399843', '0.11282173', '0.32572043', '0.36819047', '512', '488',
                      'board_images_png', '0.9843567', '0.9843567']],
                    [['st1026.png', 'knot', '0.2674017', '0.35383838', '0.39859554', '0.50976944', '512', '488', 'board_images_png', '0.9884343', '0.96366304'],
                     ['st1026.png', 'knot', '0.69417506', '0.744075', '0.34379873', '0.39051458', '512', '488', 'board_images_png', '0.97863936', '0.96366304'],
                     ['st1026.png', 'defect', '0.70078284', '0.9907891', '0.5857268', '0.6470487', '512', '488', 'board_images_png', '0.96366304', '0.96366304']],
                    [['st1524.png', 'NULL', '0', '0', '0', '0', '512', '488', 'board_images_png', '0', '0.05']]]

        class_balance = "0.6, 0.29, 0.11"
        tag_names = add_bkg_class_name(self.tag_names)
        ideal_class_balance = parse_class_balance_setting(class_balance, len(tag_names))

        all_rows, _, _ = get_top_rows(self.totag_csv_file_loc, N_ROWS, self.user_folders,
                                      self.pick_max, tag_names, ideal_class_balance)
        self.assertEqual(len(all_rows), N_FILES, 'number of rows')
        self.assertEqual(all_rows, EXPECTED, 'raw values')

    def test_create_vott_json(self):
        # prepare file
        shutil.copyfile("./totag_source2.csv", "totag.csv")

        csv_file_loc = Path('.')
        N_IMAGES = 4
        user_folders = False
        pick_max = True
        tagging_location = "."
        tag_names = add_bkg_class_name(self.tag_names)
        ideal_class_balance = parse_class_balance_setting(None, len(tag_names))
        create_vott_json(csv_file_loc, N_IMAGES, user_folders,
                         pick_max, "board_images_png",
                         tagging_location, blob_credentials = None,
                         tag_names=tag_names,
                         max_tags_per_pixel= 2,
                         config_class_balance=ideal_class_balance,
                         colors = ["#e9f1fe", "#f3e9ff"])
        self.assertEqual(filecmp.cmp('Images.json', 'Images_source.json'), True, "generated VOTT json is correct")



if __name__ == '__main__':
    unittest.main()

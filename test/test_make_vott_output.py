import unittest
import shutil
import sys
import  os
from pathlib import Path
import filecmp
from azure.storage.blob import BlockBlobService

# Allow us to import utils
config_dir = str(Path.cwd().parent / "utils")
if config_dir not in sys.path:
    sys.path.append(config_dir)
from config import Config

tag_dir = str(Path.cwd().parent / "tag")
if tag_dir not in sys.path:
    sys.path.append(tag_dir)
from download_vott_json import create_vott_json, get_top_rows, add_bkg_class_name, parse_class_balance_setting, make_vott_output

class MakeVOTTOutputTestCase(unittest.TestCase):
    def setUp(self):
        print("no-op")

    # Uncomment code below for "ond-demand' VOTT json creaation using data on blob storage
    # def test_download_catdata(self):
    #     #dowload data from tagged_Abram_small
    #     config_file = Config.parse_file( r'../workconfig.ini')
    #
    #     block_blob_service = BlockBlobService(account_name=config_file["AZURE_STORAGE_ACCOUNT"],
    #                                           account_key=config_file["AZURE_STORAGE_KEY"])
    #     container_name = config_file["image_container_name"]
    #     file_location = Path('D://temp')
    #     image_loc = 'D://temp'
    #
    #     file_location_totag = (file_location / "totag.csv")
    #     create_vott_json(file_location, num_rows=1024, user_folders = True, pick_max = True, image_loc = "", output_location = file_location,
    #                      blob_credentials=(block_blob_service, container_name),
    #                      tag_names=["human","iguana"], max_tags_per_pixel=None, config_class_balance=None, colors=None)
    #     self.assertEqual(True, True)


if __name__ == '__main__':
    unittest.main()

import re
import csv
import random
import time
from collections import defaultdict
from azure.storage.blob import BlockBlobService
import sys
sys.path.append("..")
from utils.config import Config
config_file = Config.parse_file("config.ini")
block_blob_service = BlockBlobService(account_name=config_file["AZURE_STORAGE_ACCOUNT"], account_key=config_file["AZURE_STORAGE_KEY"])
container_name = config_file["label_container_name"]
file_date = [(blob.name, blob.properties.last_modified) for blob in block_blob_service.list_blobs(container_name) if re.match(r'tagged_(.*).csv', blob.name)]
block_blob_service.get_blob_to_path(container_name, max(file_date, key=lambda x:x[1])[0], config_file["tagged_output"])
with open(config_file["tagged_output"], 'r') as file:
    reader = csv.reader(file)
    header = next(reader)
    all_preds = list(reader)
all_files=defaultdict(list)
for row in all_preds:
    all_files[row[0]].append(row)
test_num=int(len(all_files)*float(config_file["test_percentage"]))
test_tags = random.sample(all_files.items(), test_num)
flat_tags = [cur_tag for tag_list in test_tags for cur_tag in tag_list[1]]
with open(config_file["test_output"], 'w') as test_file:
    csv_writer = csv.writer(test_file)
    csv_writer.writerow(header)
    csv_writer.writerows(flat_tags)
block_blob_service.create_blob_from_path(container_name, "{}_{}.{}".format("test",int(time.time() * 1000),"csv"), config_file["test_output"])

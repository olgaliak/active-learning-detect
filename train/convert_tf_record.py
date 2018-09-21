from collections import defaultdict
import tensorflow as tf
import numpy as np
import csv
import hashlib
from pathlib import Path
import re

FOLDER_LOCATION = 8
HEIGHT_LOCATION = 6
WIDTH_LOCATION = 7

def int64_feature(value):
  return tf.train.Feature(int64_list=tf.train.Int64List(value=value))

def bytes_feature(value):
  return tf.train.Feature(bytes_list=tf.train.BytesList(value=value))

def float_feature(value):
  return tf.train.Feature(float_list=tf.train.FloatList(value=value))

def create_tf_example(predictions, raw_img, tag_map):
    filename = predictions[0][0]
    height = int(predictions[0][HEIGHT_LOCATION])
    width = int(predictions[0][WIDTH_LOCATION])
    key = hashlib.sha256(raw_img).hexdigest()
    xmin = []
    ymin = []
    xmax = []
    ymax = []
    classes = []
    classes_text = []
    truncated = []
    poses = []
    difficult_obj = []
    for prediction in predictions:
        if prediction[1]!="NULL":
            ymin.append(float(prediction[4]))
            xmin.append(float(prediction[2]))
            ymax.append(float(prediction[5]))
            xmax.append(float(prediction[3]))
            tag_name = prediction[1]
            classes_text.append(tag_name.encode('utf8'))
            classes.append(tag_map[tag_name])
            truncated.append(0)
            poses.append("Unspecified".encode('utf8'))
            difficult_obj.append(0)
    
    example = tf.train.Example(features=tf.train.Features(feature={
      'image/height': int64_feature([height]),
      'image/width': int64_feature([width]),
      'image/filename': bytes_feature([
          filename.encode('utf8')]),
      'image/source_id': bytes_feature([
          filename.encode('utf8')]),
      'image/key/sha256': bytes_feature([key.encode('utf8')]),
      'image/encoded': bytes_feature([raw_img]),
      'image/format': bytes_feature(['jpeg'.encode('utf8')]),
      'image/object/bbox/xmin': float_feature(xmin),
      'image/object/bbox/xmax': float_feature(xmax),
      'image/object/bbox/ymin': float_feature(ymin),
      'image/object/bbox/ymax': float_feature(ymax),
      'image/object/class/text': bytes_feature(classes_text),
      'image/object/class/label': int64_feature(classes),
      'image/object/difficult': int64_feature(difficult_obj),
      'image/object/truncated': int64_feature(truncated),
      'image/object/view': bytes_feature(poses),
    }))
    return example

def create_tf_record(pred_file, record_file, image_loc, user_folders, label_map_path,
                     split_names=["train","val"], split_percent=[.7,.3], tag_names = ["stamp"], test_file=None):
    
    with open(label_map_path, "w") as map_file:
      for index, name in enumerate(tag_names, 1):
          map_file.write("item {{\n  id: {}\n  name: '{}'\n}}".format(index, name))
    
    record_file = Path(record_file)
    with open(pred_file, 'r') as file:
        reader = csv.reader(file)
        next(reader, None)
        all_preds = list(reader)

    all_files = defaultdict(list)
    if test_file is not None:
        with open(test_file, 'r') as file:
            reader = csv.reader(file)
            next(reader, None)
            all_test = set((row[0] for row in reader))
        for row in all_preds:
            if row[0] not in all_test:
                all_files[row[0]].append(row)
    else:
        for row in all_preds:
            all_files[row[0]].append(row)

    rand_list = list(all_files)
    np.random.shuffle(rand_list)
    split_percent = np.cumsum(split_percent)
    split_percent = split_percent[:-1]
    split_percent *= len(rand_list)
    split_percent = split_percent.round().astype(np.int)
    split_preds = np.split(rand_list,split_percent)

    tag_map = {name: index for index, name in enumerate(tag_names, 1)}

    for name, filenames in zip(split_names, split_preds):
        writer = tf.python_io.TFRecordWriter("{}_{}".format(record_file.with_suffix(''), name) + record_file.suffix)
        for filename in filenames:
            predictions = all_files[filename]
            if user_folders:
                file_loc = str(Path(image_loc)/predictions[0][FOLDER_LOCATION]/filename)
            else:
                file_loc = str(Path(image_loc)/filename)
            with open(file_loc, "rb") as img_file:
                raw_img = img_file.read()
            tf_example = create_tf_example(predictions, raw_img, tag_map)
            writer.write(tf_example.SerializeToString())

        writer.close()

if __name__ == "__main__":
    #select_jsons(r"C:\Users\t-yapand\Desktop\GAUCC",r"C:\Users\t-yapand\Desktop\GAUCC.json",True,r"C:\Users\t-yapand\Desktop\GAUCC1_1533070038606.csv")
    from azure.storage.blob import BlockBlobService
    import sys
    import os    
    # Allow us to import utils
    config_dir = str(Path.cwd().parent / "utils")
    if config_dir not in sys.path:
        sys.path.append(config_dir)
    from config import Config
    if len(sys.argv)<2:
        raise ValueError("Need to specify config file")
    config_file = Config.parse_file(sys.argv[1])
    block_blob_service = BlockBlobService(account_name=config_file["AZURE_STORAGE_ACCOUNT"], account_key=config_file["AZURE_STORAGE_KEY"])
    container_name = config_file["label_container_name"]
    file_date = [(blob.name, blob.properties.last_modified) for blob in block_blob_service.list_blobs(container_name) if re.match(r'tagged_(.*).csv', blob.name)]
    if file_date:
        block_blob_service.get_blob_to_path(container_name, max(file_date, key=lambda x:x[1])[0], config_file["tagged_output"])
    else:
        raise ValueError("No tagged data exists. Cannot train model without any tagged data.")
    file_date = [(blob.name, blob.properties.last_modified) for blob in block_blob_service.list_blobs(container_name) if re.match(r'test_(.*).csv', blob.name)]
    if file_date:
        block_blob_service.get_blob_to_path(container_name, max(file_date, key=lambda x:x[1])[0], config_file["test_output"])
        create_tf_record(config_file["tagged_output"],config_file["tf_record_location"],config_file["image_dir"], 
            config_file["user_folders"]=="True", config_file["label_map_path"], tag_names=config_file["classes"].split(","), test_file=config_file["test_output"])
    else:
        create_tf_record(config_file["tagged_output"],config_file["tf_record_location"],config_file["image_dir"], 
            config_file["user_folders"]=="True", config_file["label_map_path"], tag_names=config_file["classes"].split(","))

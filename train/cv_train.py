from collections import defaultdict
import csv
from pathlib import Path
import re
import functools

from azure.cognitiveservices.vision.customvision.training import training_api
from azure.cognitiveservices.vision.customvision.prediction import prediction_endpoint
from azure.cognitiveservices.vision.customvision.training.models import ImageFileCreateEntry, Region

# Make sure this is less than all the API limits
IMAGE_BATCH_SIZE = 64
IMAGE_NAME_LOCATION = 0
TAG_NAME_LOCATION = 1
FOLDER_LOCATION = 8
HEIGHT_LOCATION = 6
WIDTH_LOCATION = 7
X_MIN_LOCATION = 2
X_MAX_LOCATION = 3
Y_MIN_LOCATION = 4
Y_MAX_LOCATION = 5

def calculate_confidence(predictions):
    return min([float(prediction[0]) for prediction in predictions])

def convert_row_to_region(tag_map, row):
    tag = tag_map[row[TAG_NAME_LOCATION]]
    x = float(X_MIN_LOCATION)
    y = float(Y_MIN_LOCATION)
    width = float(row[X_MAX_LOCATION]) - x
    height = float(row[Y_MAX_LOCATION])- y
    return Region(tag_id=tag.id, left=x,top=y,width=width,height=height)

def pred_to_list(prediction):
    x_min = prediction.bounding_box.left
    x_max = x_min + prediction.bounding_box.width
    y_min = prediction.bounding_box.top
    y_max = y_min + prediction.bounding_box.height
    return [prediction.probability, prediction.tag_name, y_min, x_min, y_max, x_max]

def make_csv_output(all_predictions: List[List[List[int]]], all_names: List[str], all_sizes: List[Tuple[int]], 
        untagged_output: str, tagged_output: str, file_set: AbstractSet, user_folders: bool = True):
    '''
    Convert list of Detector class predictions as well as list of image sizes
    into a dict matching the VOTT json format.
    '''
    with open(tagged_output, 'w', newline='') as tagged_file, open(untagged_output, 'w', newline='') as untagged_file:
        tagged_writer = csv.writer(tagged_file)
        untagged_writer = csv.writer(untagged_file)
        if user_folders:
            tagged_writer.writerow(["filename", "class", "xmin","xmax","ymin","ymax","height","width","folder", "box_confidence", "image_confidence"])
            untagged_writer.writerow(["filename", "class", "xmin","xmax","ymin","ymax","height","width","folder", "box_confidence", "image_confidence"])
        else:
            tagged_writer.writerow(["filename", "class", "xmin","xmax","ymin","ymax","height","width","box_confidence", "image_confidence"])
            untagged_writer.writerow(["filename", "class", "xmin","xmax","ymin","ymax","height","width","box_confidence", "image_confidence"])
        if user_folders:
            for (folder, name), predictions, (height, width) in zip(all_names, all_predictions, all_sizes):
                if not predictions:
                    predictions = [[0,"NULL",0,0,0,0]]
                else:
                    predictions = [pred_to_list(prediction) for prediction in predictions]
                confidence = calculate_confidence(predictions)
                for prediction in predictions:
                    (tagged_writer if name in file_set[folder] else untagged_writer).writerow([name,prediction[1],prediction[3],prediction[5],prediction[2],prediction[4],height,width,folder,prediction[0], confidence])
        else:
            for name, predictions, (height,width) in zip(all_names, all_predictions, all_sizes):
                if not predictions:
                    predictions = [[0,"NULL",0,0,0,0]]
                confidence = calculate_confidence(predictions)
                for prediction in predictions:
                    (tagged_writer if name in file_set else untagged_writer).writerow([name,prediction[1],prediction[3],prediction[5],prediction[2],prediction[4],height,width,prediction[0], confidence])

def create_cv_predictions(image_loc, predictor, project_id, output_file_tagged, output_file_untagged, tagged_images, tagging_images,
                                filetype, min_confidence=.2, user_folders=True):    
    basedir = Path(basedir)
    CV2_COLOR_LOAD_FLAG = 1
    all_predictions = []
    if user_folders:
        if cur_tagged is not None:
            with open(cur_tagged, 'r') as file:
                reader = csv.reader(file)
                next(reader, None)
                all_tagged = list(reader)
        if cur_tagging is not None:
            with open(cur_tagging, 'r') as file:
                reader = csv.reader(file)
                next(reader, None)
                all_tagged.extend(list(reader))
        already_tagged = defaultdict(set)
        for row in all_tagged:
            already_tagged[row[FOLDER_LOCATION]].add(row[0])
        subdirs = [subfile for subfile in basedir.iterdir() if subfile.is_dir()]
        all_names = []
        all_image_files = [] 
        all_sizes = []
        all_predictions = []
        for subdir in subdirs:
            cur_image_names = list(subdir.rglob(filetype))
            all_image_files += [str(image_name) for image_name in cur_image_names]
            foldername = subdir.stem
            all_names += [(foldername, filename.name) for filename in cur_image_names]
            for image in cur_image_names:
                with image.open(mode="rb") as img_data:
                    all_predictions.append(predictor.predict_image(project_id, img_data))
        all_sizes = [cv2.imread(image, CV2_COLOR_LOAD_FLAG).shape[:2] for image in all_image_files]
            
    else:
        with open(cur_tagged, 'r') as file:
            reader = csv.reader(file)
            next(reader, None)
            already_tagged = {row[0] for row in reader}
        with open(cur_tagging, 'r') as file:
            reader = csv.reader(file)
            next(reader, None)
            already_tagged |= {row[0] for row in reader}
        all_image_files = list(basedir.rglob(filetype))
        all_names = [filename.name for filename in all_image_files]
        all_predictions = []
        for image in all_image_files:
            with image.open(mode="rb") as img_data:
                all_predictions.append(predictor.predict_image(project_id, img_data))
        all_sizes = [cv2.imread(str(image), CV2_COLOR_LOAD_FLAG).shape[:2] for image in all_image_files]
    make_csv_output(all_predictions, all_names, all_sizes, untagged_output, tagged_output, already_tagged, user_folders)
    

def train_cv_model(pred_file, trainer, project_id, image_loc, user_folders, tag_names = ["stamp"], test_file=None):
    
    # Make sure tag_names are in custom vision and create tag_map
    all_tag_names = {tag.name:tag for tag in trainer.get_tags(project_id)}
    for tag_name in tag_names:
        if tag_name not in all_tag_names:
            all_tag_names[tag_name] = trainer.create_tag(project_id, tag_name)
    get_region = functools.partial(convert_row_to_region, all_tag_names)

    num_tagged_images = trainer.get_tagged_image_count(project_id)
    all_images = []
    for num_to_skip in range(0, num_tagged_images, IMAGE_BATCH_SIZE):
        all_images+=get_tagged_images(project_id, take=IMAGE_BATCH_SIZE, skip=num_to_skip)
    all_existing_image_names = set(image.id for image in all_images)

    with open(pred_file, 'r') as file:
        reader = csv.reader(file)
        next(reader, None)
        all_preds = list(reader)

    all_train = defaultdict(list)
    if user_folders:
        if test_file is not None:
            with open(test_file, 'r') as file:
                testreader = csv.reader(file)
                next(reader, None)
                all_test = set(row[IMAGE_NAME_LOCATION]+"/"+row[FOLDER_LOCATION] for row in testreader)
            for row in all_preds:
                if row[0] not in all_test:
                    all_train[row[IMAGE_NAME_LOCATION]+"/"+row[FOLDER_LOCATION]].append(row)

            # Remove images from test set that are in custom vision training set
            images_to_delete = []
            for image_name in all_test:
                if image_name in all_existing_image_names:
                    images_to_delete.append(image_name)
            for cur_index in range(0,len(images_to_delete),IMAGE_BATCH_SIZE):
                trainer.delete_images(project_id, images_to_delete[cur_index:cur_index+IMAGE_BATCH_SIZE])

        else:
            for row in all_preds:
                all_train[row[IMAGE_NAME_LOCATION]+"/"+row[FOLDER_LOCATION]].append(row)

        # Add images from training set that are not yet in custom vision training set
        to_upload = []
        for image_name, information in all_train.items():
            regions = [get_region(row) for row in information]
            with Path(image_loc)/information[0][FOLDER_LOCATION]/information[0][IMAGE_NAME_LOCATION].open(mode="rb") as image_contents:
                to_upload.append(ImageFileCreateEntry(name=image_name, contents=image_contents.read(), regions=regions))
        for cur_index in range(0,len(to_upload),IMAGE_BATCH_SIZE):
            trainer.create_images_from_files(project_id, images=to_upload[cur_index:cur_index+IMAGE_BATCH_SIZE])

    else:
        if test_file is not None:
            with open(test_file, 'r') as file:
                testreader = csv.reader(file)
                next(reader, None)
                all_test = set(row[IMAGE_NAME_LOCATION] for row in testreader)
            for row in all_preds:
                if row[IMAGE_NAME_LOCATION] not in all_test:
                    all_train[row[IMAGE_NAME_LOCATION]].append(row)
            
            # Remove images from test set that are in custom vision training set
            images_to_delete = []
            for image_name in all_test:
                if image_name in all_existing_image_names:
                    images_to_delete.append(image_name)
            for cur_index in range(0,len(images_to_delete),IMAGE_BATCH_SIZE):
                trainer.delete_images(project_id, images_to_delete[cur_index:cur_index+IMAGE_BATCH_SIZE])

        else:
            for row in all_preds:
                all_train[row[IMAGE_NAME_LOCATION]].append(row)

        # Add images from training set that are not yet in custom vision training set
        to_upload = []
        for image_name, information in all_train.items():
            regions = [get_region(row) for row in information]
            with Path(image_loc)/image_name.open(mode="rb") as image_contents:
                to_upload.append(ImageFileCreateEntry(name=image_name, contents=image_contents.read(), regions=regions))
        for cur_index in range(0,len(to_upload),IMAGE_BATCH_SIZE):
            trainer.create_images_from_files(project_id, images=to_upload[cur_index:cur_index+IMAGE_BATCH_SIZE])

    print ("Training...")
    iteration = trainer.train_project(project.id)
    while (iteration.status != "Completed"):
        iteration = trainer.get_iteration(project.id, iteration.id)
        print ("Training status: " + iteration.status)
        time.sleep(1)

    # The iteration is now trained. Make it the default project endpoint
    trainer.update_iteration(project.id, iteration.id, is_default=True)
    print ("Done!")


if __name__ == "__main__":
    from azure.storage.blob import BlockBlobService
    import sys
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

    from map_validation import detectortest
    file_date = [(blob.name, blob.properties.last_modified) for blob in block_blob_service.list_blobs(container_name) if re.match(r'test_(.*).csv', blob.name)]
    if file_date:
        block_blob_service.get_blob_to_path(container_name, max(file_date, key=lambda x:x[1])[0], config_file["test_output"])
        train_cv_model(config_file["tagged_output"],config_file["tf_record_location"],config_file["image_dir"], 
            config_file["user_folders"]=="True", tag_names=config_file["classes"].split(","), test_file=config_file["test_output"])
        detectortest(config_file["tagged_predictions"], config_file["test_output"], config_file["validation_output"], config_file["user_folders"]=="True")
    else:
        train_cv_model(config_file["tagged_output"],config_file["tf_record_location"],config_file["image_dir"], 
            config_file["user_folders"]=="True", tag_names=config_file["classes"].split(","))
        detectortest(config_file["tagged_predictions"], config_file["tagged_output"], config_file["validation_output"], config_file["user_folders"]=="True")

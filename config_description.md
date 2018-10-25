# Guide to config.ini
As config.ini has many values to fill out, this guide is intended to help provide more details between what each variable means and how to choose the right value. The guide is organized by sections in the config file. Note that the Azure Storage Account Information and Image Information need to be filled in for both tagging and training machines, while for the remaining sections only those corresponding to the type of machine must be filled.
## Azure Storage Account Information
As described in the readme, azure blob storage containers are used to store image and label data as well as trained model inference graph and performance files. To connect to the azure storage account, both the account name and an access key are required. Furthermore, the storage account needs to have separate containers to store images and to store label data.
- AZURE_STORAGE_ACCOUNT:
This is the azure blob storage account name.
- AZURE_STORAGE_KEY:
This is a valid access key for the blob storage account.
- image_container_name:
This is the name of the container within the blob storage account that holds all images.
- label_container_name:
This is the name of the container within the blob storage that holds all label and model data.
## Image Information
Certain information about the images is required before the tagging and training process can begin. This is mainly so that the right images can be found and so the right tag names are used.
- user_folders:
This determines whether or not the images in blob storage are within separate folders (e.g. by date or by weather condition). Set to True if they are, False if not.
- classes:
This is a comma separated list of all classes that are being tagged. Please ensure that there are no spaces in the list and only commas are used to separate names.
- ideal_class_balance
This is a comma separated list of requested classes distribution in images being reviewed by human expert.  
Example (for 2-class scenario):  
`ideal_class_balance=0.6,0.3,0.1`  
In this example:  
  60% of images that use will be reviewing will have at least one bbox with object class1,   
  30%  images that have  bboxes for class  (defects),  
  10% of images get class "NULL" -- were neither knots nor defects were detected by the model.

- filetype:
This is the type of image file used. The format is a glob pattern, so *.jpg for a .jpg file or *.png for a .png file. Note that only JPEG or PNG filetypes can be used with tensorflow.
## Tagging Machine
These are variables that must be set (along with azure storage information and image information) on the config.ini file for the tagging machine. They are not needed on a training machine.
- tagging_location:
This is the folder where all images will be downloaded and the VOTT .json file will be created. Please ensure that this folder is empty so that there are no conflicts while downloading/uploading. The folder will be created automatically if it does not exist.
- pick_max:
This determines whether the images with lowest or highest confidence are chosen to be labelled. Only set it to True if you wish to evaluate images where your model is very confident to ensure that it is not learning incorrect patterns with high confidence. Otherwise, keep it at the default value of False.
- max_tags_per_pixel:
This limits the number of tags per pixel, preventing too many duplicate tags.
## Custom Vision
These variables are all available at customvision.ai if you select the settings icon.
- training_key:
This is your Custom Vision training key.
- prediction_key:
This is your Custom Vision prediction key.
- project_id:
This is the project ID for an **object detection** project in custom vision. You can create a new one by selecting the New Project button.
## Training Machine
These are variables that must be set (along with azure storage information and image information) on the config.ini file for the training machine. They are not needed on a tagging machine.
### Locations
These variables deal with the location that data and files are kept on the tagging machine. These are needed to ensure that the right python files are being called and that active learning data is not interfering with other data on the machine.
- python_file_directory:
This is the directory housing all the python files from the active-learning-detect repository. It will be in train folder within the directory where the active-learning-detect repository was cloned.
- data_dir:
This is where all images and label files will be downloaded. Please ensure that this directory is empty / does not currently exist and that the disk it is hosted on has enough free space for all the images in blob storage.
- train_dir:
This is where tensorflow will update information while it is training. It can be used to visualize training using tensorboard through the command tensorboard --logdir ${train_dir}. This directory will be deleted if it already exists, so please ensure that it either does not exist or is empty.
- inference_output_dir:
This is where tensorflow will export the inference graph that saves the state of the model and is used for inference. Again, please ensure that the location is empty and that it contains enough space for an inference graph (up to ~100mb for large models).
- tf_models_location:
This is where the tensorflow models repository has been cloned. Please point to the research folder within the repository, as that is where all the necessary files are located.
- download_location:
This is where the tensorflow pretrained model and pipeline.config is stored. If this does not already exist, then this is where the model is downloaded form the tensorflow model zoo.
### Training
This information relates to training the model. It includes the type of model to use and how to train and predict using the model.
- train_iterations:
This is how many iterations to train the model. More iterations can improve performance of the model, but may take longer and lead to model overfitting.
- eval_iterations:
This is how many iterations of evaluation to run on the model. Evaluation is run using the validation set.
- min_confidence:
This is the minimum confidence with which a prediction is considered a valid prediction. This is to prevent predictions with very low confidence from being considered valid.
- test_percentage:
This is the percentage of the data to split into a separate test set. Note that the test set can be repartitioned using the repartition_test_set.py file within the train folder.
- model_name:
This is the name of the pretrained model to use for transfer learning. This model is automatically downloaded from the [tensorflow model zoo](https://github.com/tensorflow/models/blob/master/research/object_detection/g3doc/detection_model_zoo.md) if it does not already exist in the download_location.
- optional_pipeline_url:
This is an optional parameter that can be used to override the pipeline.config file in the pretrained model. We suggest using the [sample config files](https://github.com/tensorflow/models/tree/master/research/object_detection/samples/configs) over the ones from model zoo as the model zoo files are not kept updated with newer releases of tensorflow and may cause training to fail.
### Config File Details
These parameters are used to replace certain parts of the pipeline.config file to match current settings. You may need to change some parameters every time you choose a different pipeline.config file. The last three values will likely not change.
- old_label_path:
This is the label path previously set in the pipeline.config file. It will be replaced with the current path to the label map file.
- old_train_path:
This is the path to the TF record file containing training data previously set in the pipeline.config file. It will be replaced with the path to a TF record file generated from the most recent set of tagged data.
- old_val_path:
This is the path to the TF record file containing validation data previously set in the pipeline.config file. It will be replaced with the path to a TF record file generated from the most recent set of tagged data.
- old_checkpoint_path:
This is the path to a previous model checkpoint previously set in the pipeline.config file. It will be replaced with a path to the model that is being used for transfer learning.
- num_examples_marker:
This is the marker used to designate the number of examples. The number after it will be changed to the number of examples in the evaluation file.
- num_steps_marker:
This is the marker used to designate the number of training steps. The number after it will be changed to the number of steps defined in train_iterations.
- num_classes_marker:
This the the marker used to designate the number of classes. The number after it will be replaced with the number of classes specified in classes.

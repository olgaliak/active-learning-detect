# Active learning + object detection.
Let's use wood knots data set as example: the goal label the data and to train the model that can detect wood knots. 
As we label the data we want optimize human efforts by leveraging ML to pre-label the data.
The flow will be:
1) Label small set of data (Set #1) to train simple but already somewhat useful model  that can detect objects of interest (wood knots).
   In the case with woodknots spening aroudn 1h and going though 150 images will be enough. I used VOTT tool for bounding boxes drawing.
2) Train Model #1
3) Now select bigger set of images that were not used in Set #1. This will be our Set #2.
4) User Model #1 for inference on Set #2: the models should be able to detect quite a bit objects of interest.
5) Load object detection results from previous step into the labeling tool (VOTT).
6) Now istead of "labeling from scratch" human will much quicker review detection results from Model #1 and make small adjustments.
7) Combine training Set #1 and Set #2. Train Model #2. Observe how Model #2 overall performance increases. Celebrate :).

# Code setup
The process in this repo hevily relies on Tensorflow Object Detection API.  So as pre-req make sure you have it working on the samples.
Further below I assume you cloned TF object detection to a location like:
`repo\models`
1)  Create TF records for training (and evaluation: use --set=val param)

`python create_knots_tf_record.py  --data_dir=C:\data\woodknots\board_images_png_output --output_path=knots_train.record --set=train --label_map_path=C:\data\woodknots\board_images_png_output\pascal_label_map.pbtxt`

As you run VOTT for labeling and export result you will have YOU_FOLDER_WITH_IMAGES_output and inside it there will be pascal_label_map.pbtxt

Note: I'm running _create_knots_tf_record.py_ from within _repo\models\research_

2) Train Model #1 using TF Object Detection
`python train.py --logtostderr --train_dir=.object_detection\knot_models --pipeline_config_path=object_detection\samples\configs\faster_rcnn_resnet50_knots.config`

Note: I based _faster_rcnn_resnet50_knots.config_ on _faster_rcnn_resnet50_pets.config_.  I made the following changes: 

a) Set _num_classes_ appropriately (3 in my case: knots, other wood defects and background)

b) Set _fine_tune_checkpoint_ to point to the location of _faster_rcnn_resnet50_coco_2018_01_28_ model in my file system. Something like this: 
`C:\\repo\\models\\research\\object_detection\\faster_rcnn_resnet50_coco_2018_01_28\\faster_rcnn_resnet50_coco_2018_01_28\\model.ckpt`

c) Lowered _num_steps_ to 10000

d) Added more data augmentation options:
`data_augmentation_options {
    random_horizontal_flip {
    }
    random_crop_image {
    }
    random_image_scale {    
    }
  }`

 e) Updated _input_path_ and _label_map_path_ for training and evaluation.

 3)  Export inference graph

 `python export_inference_graph.py --input_type image_tensor --pipeline_config_path object_detection\samples\configs\faster_rcnn_resnet50_knots.config --trained_checkpoint_prefix object_detection\knot_models\model.ckpt-10000 --output_directory .\fine_tuned_model_set1_10k`

4)  Run evaluation (so later you can compare Model #1 and Model #2)

`python eval.py --logtostderr  --pipeline_config_path object_detection\samples\configs\faster_rcnn_resnet50_knots.config --checkpoint_dir=object_detection\knot_models_10000     --eval_dir=eval_10000`

5) Copy _active_learning_ folder to _repo\models\research\object_detection_

6) Set active-learning-detect\detect_object.py to use Model #1

`   PATH_Fold = "C:\\repo\\models\\research\\fine_tuned_model_set1_10k\\"
    PATH_TO_CKPT = PATH_Fold + 'frozen_inference_graph.pb'`

7) Use Model #1 to detect objects in Set #2: execute _object_detection\active-learning-detect\run_detection.py_.  Set input to be folder with Set #2 images.

The results of detection will be saved in csv file: woodknots_detection_log.csv. Each row in the csv file contaings location of the detected object and its class.

8) Next step is about conerting csv file with detection results to the format supported labeling tool of choice.

For using VOTT run this script: 

`\object_detection\active-learning-detect\convert_vott.py --input "C:\data\woodknots\set2_res\woodknots_detection_log.csv" --output "C:\data\woodknots\set2_res\vott.json"`

9) Now you have Set #2 pre-labeled.  To load it to VOTT copy _vott.json_ from previous step to the same level as your FOLDER_WITH_SET2_IMAGES and rename vott.json to _FOLDER_WITH_SET2_IMAGES.json_. Then start VOTT, load FOLDER_WITH_SET2_IMAGES for tagging, review pre-labled info, fix lables.

10) Once you get your Set2 labeled you will repeat the step of coverting dataset (now with SET #2) to tfrecords.

Then train Model #2 on bigger dataset (Set #1 combined with Set #2).  You can specify multiple source files for training in _faster_rcnn_resnet50_knots.config_ by reading all files in a train directory:

`tf_record_input_reader {
    input_path: "C:\\knots_data\\train\\*"
  }`
  


import numpy as np
import os
import glob
import cv2
import six.moves.urllib as urllib
import sys
import tarfile
import tensorflow as tf
import config
import time

sys.path.append("..")

from object_detection.utils import label_map_util

# set to one GPU machine
os.environ["CUDA_VISIBLE_DEVICES"]="1"

def detect(input_dir,
           output_dir,
	   model_name,
           use_sample = config.DetectConfig.use_sample,
           use_relative_size = config.DetectConfig.use_relative_size):
    detection_metadata_fn = os.path.join(output_dir, config.config.DETS_FILE)
    print("Starting detection {}, output {}, scale {}". format(input_dir, detection_metadata_fn, config.DetectConfig.SCALE_RATIO))

    # Path to frozen detection graph. This is the actual model that is used for the object detection.
    PATH_Fold = "C:\\Users\\olgali\\repo\\models\\research\\fine_tuned_model_set1_10k\\"
    PATH_TO_CKPT = PATH_Fold + 'frozen_inference_graph.pb'

    # List of the strings that is used to add correct label for each box.
    PATH_TO_LABELS = os.path.join('C:\\data\\woodknots\\board_images_set1_output', 'pascal_label_map.pbtxt')

    NUM_CLASSES = 2

    ## Load a (frozen) Tensorflow model into memory
    detection_graph = tf.Graph()
    with detection_graph.as_default():
        od_graph_def = tf.GraphDef()
        with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
            serialized_graph = fid.read()
            od_graph_def.ParseFromString(serialized_graph)
            tf.import_graph_def(od_graph_def, name='')

    ## Loading label map
    label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
    categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES, use_display_name=True)
    category_index = label_map_util.create_category_index(categories)

    ## Helper code
    def load_image_into_numpy_array(image):
      (im_width, im_height) = image.size
      return np.array(image.getdata()).reshape(
          (im_height, im_width, 3)).astype(np.uint8)

    #============================ Detection ============================
    start_time = time.time()
    raw_img_name = next(os.walk(input_dir))[2][0]
    fn_img, ext = os.path.splitext(os.path.basename(raw_img_name))
    raw_img = cv2.imread(os.path.join(input_dir, raw_img_name))
    raw_im_height, raw_im_width = raw_img.shape[0:2]

    print("Reading frames...")
    if config.DetectConfig.SCALE_RATIO < 1:
        im_height, im_width = int(raw_im_height*config.DetectConfig.SCALE_RATIO), int(raw_im_width*config.DetectConfig.SCALE_RATIO)
        images, image_names = zip(*[(cv2.resize(cv2.imread(file), (im_height, im_width)), file.split('/')[-1]) for file in glob.glob(input_dir + '/*' + ext)])
    else:
        im_height, im_width = raw_im_height, raw_im_width
        images, image_names = zip(*[(cv2.imread(file), file.split('/')[-1]) for file in glob.glob(input_dir + '/*' + ext)])

    images = np.array(images)
    image_names = list(image_names)
    if (use_sample == 1):
        print("Using sample size: ", config.DetectConfig.SAMPLE_SIZE)
        images = images[:config.DetectConfig.SAMPLE_SIZE]
        image_names = image_names[:config.DetectConfig.SAMPLE_SIZE]


    boxes_total = np.zeros(shape = (len(images), 300, 4))
    scores_total =  np.zeros(shape = (len(images), 300))
    classes_total = np.zeros(shape = (len(images), 300))

    with detection_graph.as_default():
        with tf.Session(graph=detection_graph) as sess:
            # Definite input and output Tensors for detection_graph
            image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')
            # Each box represents a part of the image where a particular object was detected.
            detection_boxes = detection_graph.get_tensor_by_name('detection_boxes:0')
            # Each score represent how level of confidence for each of the objects.
            # Score is shown on the result image, together with the class label.
            detection_scores = detection_graph.get_tensor_by_name('detection_scores:0')
            detection_classes = detection_graph.get_tensor_by_name('detection_classes:0')
            num_detections = detection_graph.get_tensor_by_name('num_detections:0')

            for i in range(0, len(images), config.DetectConfig.BATCH_SIZE):
                feed_images = np.array(images[i:i+config.DetectConfig.BATCH_SIZE])
                (boxes, scores, classes, num) = sess.run(
                  [detection_boxes, detection_scores, detection_classes, num_detections],
                  feed_dict={image_tensor: feed_images})
                boxes_total[i:i+config.DetectConfig.BATCH_SIZE] = boxes
                scores_total[i:i+config.DetectConfig.BATCH_SIZE] = scores
                classes_total[i:i+config.DetectConfig.BATCH_SIZE] = classes
  
    print("--- %s seconds ---" % (time.time() - start_time))
    #============================ Post-processing ============================
    all_dets = []
    skipped_dets = 0
    for i in range(len(images)):
        image_name = os.path.basename(image_names[i])
        per_score = scores_total[i]
        per_class = classes_total[i]
        per_box = boxes_total[i]
        ind = np.where(per_score >= config.DetectConfig.MIN_SCORE_THRESH)
        #print("Found {} boxes for class {}".format(len(ind[0]), config.config.CLASSES_DICT))

        saved_detection = 0
        for i in ind[0]:
            bbox_height = abs(per_box[i][0] - per_box[i][2])*im_height
            if bbox_height < config.DetectConfig.MIN_DETECT_HEIGHT:
                skipped_dets = skipped_dets + 1
                continue
            if use_relative_size:
                bbox = per_box[i]
            else:
                bbox = [ per_box[i][1]*im_width, per_box[i][0]*im_height, per_box[i][3]*im_width,per_box[i][2]*im_height]

            all_dets.append(image_name+','+str(config.config.CLASSES_DICT[per_class[i]]) + ',' + str(per_score[i]) + ',' +
                            ','.join(map(str,bbox)) + ','
                            + str(im_width) + ',' + str(im_height))
            saved_detection = 1
        # Handle images that did not have any detections
        if not saved_detection:
            bbox = [0, 0, 0, 0]
            all_dets.append(
                image_name + ',' + config.DetectConfig.CLASS_NA + ',' + str(0) + ',' +
                ','.join(map(str, bbox)) + ','
                + str(im_width) + ',' + str(im_height))

    ## Save to log file
    out = open(detection_metadata_fn, 'w')
    line = 'image,class,score,bbox_0,bbox_1,bbox_2,bbox_3,im_width,im_height'
    out.write("%s\n" % line)

    for line in all_dets:
        out.write("%s\n" % line)
    out.flush()

    out.close()

    print("Skipped {0} detections which heights is less than {1}". format(skipped_dets, config.DetectConfig.MIN_DETECT_HEIGHT))

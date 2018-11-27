import numpy as np
import tensorflow as tf


class TFDetector():

    def __init__(self, classes, inference_graph="frozen_graph.pb"):
        '''Initialize Detector Object'''
        super().__init__()
        self.label_arr = np.asarray(["NULL"]+classes)
        path_to_ckpt = inference_graph
        self.detection_graph = tf.Graph()
        with self.detection_graph.as_default():
            od_graph_def = tf.GraphDef()
            with tf.gfile.GFile(path_to_ckpt, 'rb') as fid:
                serialized_graph = fid.read()
                od_graph_def.ParseFromString(serialized_graph)
                tf.import_graph_def(od_graph_def, name='')
    
    def predict(self, images_data, batch_size=10, min_confidence=.7):
        '''Predict results from list of images to list of boxes'''
        with self.detection_graph.as_default():
            with tf.Session() as sess:
                ops = tf.get_default_graph().get_operations()
                all_tensor_names = {output.name for op in ops for output in op.outputs}
                tensor_dict = {}
                for key in ['detection_boxes','detection_scores','detection_classes']:
                    tensor_name = key + ':0'
                    if tensor_name in all_tensor_names:
                        tensor_dict[key] = tf.get_default_graph().get_tensor_by_name(
                            tensor_name)
                image_tensor = tf.get_default_graph().get_tensor_by_name('image_tensor:0')
                split_data = [images_data[i:i+batch_size] for i in range(0,images_data.shape[0],batch_size)]
                split_data = [sess.run(tensor_dict, feed_dict={image_tensor: batch}) for batch in split_data]
                split_data = [np.dstack((batch['detection_scores'],
                              self.label_arr[batch['detection_classes'].astype(np.uint8)],
                              batch['detection_boxes'])) for batch in split_data]
                combined = np.concatenate(split_data)
                non_zero = combined[:,:,0].astype(np.float)>min_confidence
        return [sorted(cur_combined[cur_non_zero].tolist(), reverse=True) for cur_combined, cur_non_zero in zip(combined, non_zero)]



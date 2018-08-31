import numpy as np
import tensorflow as tf
from pathlib import Path
import cv2
def decode_record(record_file, output_folder):
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)
    record_iterator = tf.python_io.tf_record_iterator(record_file)
    for string_record in record_iterator:
        example = tf.train.Example()
        example.ParseFromString(string_record)
            
        filename = example.features.feature['image/filename']
                                   .bytes_list
                                   .value[0].decode("utf-8")

        height = int(example.features.feature['image/height']
                                    .int64_list
                                    .value[0])
          
        width = int(example.features.feature['image/width']
                                    .int64_list
                                    .value[0])
         
        img_raw = (example.features.feature['image/encoded']
                                    .bytes_list
                                    .value[0])
        img_raw = np.fromstring(img_raw, dtype=np.uint8)
        cv2_image = cv2.imdecode(img_raw, cv2.IMREAD_COLOR)
        cv2.imwrite(str(output_folder/filename),cv2_image)
if __name__ == "__main__":
    if len(sys.argv)<3:
        raise ValueError("Need to specify input file and output folder")
    input_file = sys.argv[1]
    output_folder = sys.argv[2]
    decode_record(input_file, output_folder)

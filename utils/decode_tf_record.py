import numpy as np
import tensorflow as tf

def decode_record(filename):
    
        reconstructed_images = []

        record_iterator = tf.python_io.tf_record_iterator(path=filename)

        for string_record in record_iterator:
            
            example = tf.train.Example()
            example.ParseFromString(string_record)
            
            height = int(example.features.feature['image/height']
                                        .int64_list
                                        .value[0])
            
            width = int(example.features.feature['image/width']
                                        .int64_list
                                        .value[0])
            
            img_string = (example.features.feature['image/encoded']
                                        .bytes_list
                                        .value[0])

            img_string = (example.features.feature['image_raw']
                                        .bytes_list
                                        .value[0])

            # img_string = (example.features.feature['image_raw']
            #                             .bytes_list
            #                             .value[0])

            # annotation_string = (example.features.feature['mask_raw']
            #                             .bytes_list
            #                             .value[0])
            
            img_1d = np.fromstring(img_string, dtype=np.uint8)
            reconstructed_img = img_1d.reshape((height, width, -1))
            
            # annotation_1d = np.fromstring(annotation_string, dtype=np.uint8)
            
            # Annotations don't have depth (3rd dimension)
            #reconstructed_annotation = annotation_1d.reshape((height, width))
            
            #reconstructed_images.append((reconstructed_img, reconstructed_annotation))
            reconstructed_images.append(reconstructed_img)
if __name__ == "__main__":
    import sys
    config_dir = str(Path.cwd().parent / "utils")
    if config_dir not in sys.path:
        sys.path.append(config_dir)
    from config import Config
    if len(sys.argv)<2:
        raise ValueError("Need to specify config file")
    config_file = Config.parse_file(sys.argv[1])
    decode_record(config_file["tf_record_location"])

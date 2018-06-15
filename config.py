

class config:
	DETS_FILE = 'woodknots_detection_log.csv'
	METADATA_JSON = 'metadata.json'
	CROPS_DIR = "cropped"
	REDACTED_DIR = "redacted"
	OUTPUT_DIR = "output"
	MIN_CROP_DIM = 20
	CROP_CLASS = "knot"

	OUTPUT_CLASSES = ['knot','defect']
	ID_CLASSES = [1,2]
	CLASSES_DICT = dict(zip(ID_CLASSES, OUTPUT_CLASSES))

	SCALE_RATIO =1
	CAR_ID = "car1"
	DEVICE_ID = "dev0"
	FILE_FORMAT = "{0}_{1}_{2}_{3}{4}" # carName, deviceName, timestamp, orig_fn, extension"


# class VideoConfig(config):
# 	# dpi = 100
# 	# COL_CYAN  = (0, 255, 255)
# 	# OUT_COLORS_CV2 = [COL_CYAN]
# 	# TH_MODE = 0


class DetectConfig(config):
	MIN_SCORE_THRESH = 0.7
	BATCH_SIZE = 1
	SAMPLE_SIZE = 10
	MIN_DETECT_HEIGHT = 15
	use_sample = 0
	use_relative_size = 1
	CLASS_NA = 'na'


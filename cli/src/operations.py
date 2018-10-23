DEFAULT_NUM_IMAGES = 40
LOWER_LIMIT = 0
UPPER_LIMIT = 100


class MissingConfigException(Exception):
    pass


class ImageLimitException(Exception):
    pass


def init(config):
    if (config is None):
        raise MissingConfigException()

    raise NotImplementedError


def download(num_images):
    images_to_download = num_images

    if num_images is None:
        images_to_download = DEFAULT_NUM_IMAGES

    if images_to_download <= LOWER_LIMIT or images_to_download > UPPER_LIMIT:
        raise ImageLimitException()

    return images_to_download


def upload():
    raise NotImplementedError()


def abandon():
    raise NotImplementedError()

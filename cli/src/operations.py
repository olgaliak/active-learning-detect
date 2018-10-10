DEFAULT_NUM_IMAGES = 40


class MissingConfigException(Exception):
    pass


def init(config):
    if (config is None):
        raise MissingConfigException()

    raise NotImplementedError


def download(num_images):
    if (num_images is None):
        return DEFAULT_NUM_IMAGES

    return num_images


def upload():
    raise NotImplementedError()


def abandon():
    raise NotImplementedError()

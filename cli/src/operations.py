import configparser
import requests
import time
from azure.storage.blob import BlockBlobService

FUNCTIONS_SECTION = 'FUNCTIONS'
FUNCTIONS_KEY = 'FUNCTIONS_KEY'
FUNCTIONS_URL = 'FUNCTIONS_URL'

STORAGE_SECTION = 'STORAGE'
STORAGE_KEY = 'STORAGE_KEY'
STORAGE_ACCOUNT = 'STORAGE_ACCOUNT'
STORAGE_CONTAINER = 'STORAGE_CONTAINER'


DEFAULT_NUM_IMAGES = 40
LOWER_LIMIT = 0
UPPER_LIMIT = 100

CONFIG_PATH = "./config.ini"

azure_storage_client = None


class MissingConfigException(Exception):
    pass


class ImageLimitException(Exception):
    pass


def get_azure_storage_client(config):
    global azure_storage_client

    if azure_storage_client is not None:
        return azure_storage_client

    azure_storage_client = BlockBlobService(
        config.get("storage_account"),
        account_key=config.get("storage_key")
    )

    return azure_storage_client


def build_url(config):
    code = config.get("key")
    url = config.get("url")

    return url + "?code=" + code


def _download_bounds(num_images):
    images_to_download = num_images

    if num_images is None:
        images_to_download = DEFAULT_NUM_IMAGES

    if images_to_download <= LOWER_LIMIT or images_to_download > UPPER_LIMIT:
        raise ImageLimitException()

    return images_to_download


def download(config, num_images):
    images_to_download = _download_bounds(num_images)
    functions_url = config.get("url")

    response = requests.get(functions_url + "?imageCount=" + str(num_images))
    print(response.text)
    return images_to_download


def upload(config):
    storage_container = config.get("storage_container")
    storage_client = get_azure_storage_client(config)

    print("Uploading… VOTT json file")

    storage_client.create_blob_from_path(
        storage_container,
        "vott",
        "./images/vott.json"
    )

    print("Done!")


def read_config(config_path):
    parser = configparser.ConfigParser()
    parser.read(config_path)
    return read_config_with_parsed_config(parser)


def read_config_with_parsed_config(parser):
    sections = parser.sections()

    if FUNCTIONS_SECTION not in sections or STORAGE_SECTION not in sections:
        raise MissingConfigException()

    functions_config_section = parser[FUNCTIONS_SECTION]
    storage_config_section = parser[STORAGE_SECTION]

    functions_key_value = functions_config_section.get(FUNCTIONS_KEY)
    functions_url_value = functions_config_section.get(FUNCTIONS_URL)

    storage_account_value = storage_config_section.get(STORAGE_ACCOUNT)
    storage_key_value = storage_config_section.get(STORAGE_KEY)
    storage_container_value = storage_config_section.get(STORAGE_CONTAINER)

    if not functions_key_value or not functions_url_value:
        raise MissingConfigException()

    if not storage_account_value or not storage_key_value or not storage_container_value:
        raise MissingConfigException()

    return {
        "key": functions_key_value,
        "url": functions_url_value,
        "storage_account": storage_account_value,
        "storage_key": storage_key_value,
        "storage_container": STORAGE_CONTAINER
    }

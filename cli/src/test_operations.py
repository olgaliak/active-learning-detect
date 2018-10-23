import unittest
from operations import (
    init,
    download,
    upload,
    abandon,
    MissingConfigException,
    ImageLimitException,
    DEFAULT_NUM_IMAGES,
    LOWER_LIMIT,
    UPPER_LIMIT
)


class TestCLIOperations(unittest.TestCase):
    def test_init(self):
        with self.assertRaises(NotImplementedError):
            init("fakeconfig")

    def test_init_missing_config(self):
        with self.assertRaises(MissingConfigException):
            init(None)

    def test_download_under_limit(self):
        with self.assertRaises(ImageLimitException):
            download(LOWER_LIMIT)

    def test_download_over_limit(self):
        with self.assertRaises(ImageLimitException):
            download(UPPER_LIMIT + 1)

    def test_download_missing_image_count(self):
        downloaded_image_count = download(None)
        self.assertEqual(DEFAULT_NUM_IMAGES, downloaded_image_count)

    def test_download_with_image_count(self):
        downloaded_image_count = download(10)
        self.assertEqual(10, downloaded_image_count)

    def test_upload(self):
        with self.assertRaises(NotImplementedError):
            upload()

    def test_abandon(self):
        with self.assertRaises(NotImplementedError):
            abandon()

if __name__ == '__main__':
    unittest.main()
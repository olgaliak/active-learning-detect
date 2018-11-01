import unittest
import json
import pathlib
from unittest.mock import Mock

from operations import (
    _download_bounds,
    upload,
    read_config_with_parsed_config,
    MissingConfigException,
    ImageLimitException,
    DEFAULT_NUM_IMAGES,
    LOWER_LIMIT,
    UPPER_LIMIT,
    FUNCTIONS_SECTION,
    FUNCTIONS_KEY,
    FUNCTIONS_URL,
    STORAGE_SECTION,
    STORAGE_KEY,
    STORAGE_ACCOUNT,
    STORAGE_CONTAINER,
    TAGGING_SECTION,
    TAGGING_LOCATION_KEY,
    functions_config_section,
    storage_config_section,
    tagging_config_section,
    prepend_file_paths,
    trim_file_paths
)


class TestCLIOperations(unittest.TestCase):

    def test_download_bounds_under_limit(self):
        with self.assertRaises(ImageLimitException):
            _download_bounds(LOWER_LIMIT)

    def test_download_bounds_over_limit(self):
        with self.assertRaises(ImageLimitException):
            _download_bounds(UPPER_LIMIT + 1)

    def test_download_bounds_missing_image_count(self):
        downloaded_image_count = _download_bounds(None)
        self.assertEqual(DEFAULT_NUM_IMAGES, downloaded_image_count)

    def test_download_bounds_with_image_count(self):
        downloaded_image_count = _download_bounds(10)
        self.assertEqual(10, downloaded_image_count)


class TestConfig(unittest.TestCase):

    def _mock_sections(self, sections, data):
        def sections_function():
            return sections

        def data_function(self, name):
            return data.get(name, None)

        test = Mock()
        test.sections = sections_function
        test.__getitem__ = data_function

        return test

    def test_missing_storage_section(self):
        with self.assertRaises(MissingConfigException):
            read_config_with_parsed_config(
                self._mock_sections([FUNCTIONS_SECTION], {})
            )

    def test_missing_functions_section(self):
        with self.assertRaises(MissingConfigException):
            read_config_with_parsed_config(
                self._mock_sections([STORAGE_SECTION], {})
            )

    def test_missing_tagging_section(self):
        with self.assertRaises(MissingConfigException):
            read_config_with_parsed_config(
                self._mock_sections([FUNCTIONS_SECTION, STORAGE_SECTION], {})
            )

    def test_missing_functions_config_values(self):
        with self.assertRaises(MissingConfigException):
            functions_config_section({})

    def test_missing_storage_config_values(self):
        with self.assertRaises(MissingConfigException):
            storage_config_section({})

    def test_missing_tagging_config_values(self):
        with self.assertRaises(MissingConfigException):
            tagging_config_section({})

    def test_acceptable_config(self):
        mock_data = self._mock_sections(
            [STORAGE_SECTION, FUNCTIONS_SECTION, TAGGING_SECTION],
            {
                STORAGE_SECTION: {
                    STORAGE_KEY: "test",
                    STORAGE_ACCOUNT: "test",
                    STORAGE_CONTAINER: "test",
                },
                FUNCTIONS_SECTION: {
                    FUNCTIONS_KEY: "test",
                    FUNCTIONS_URL: "test"
                },
                TAGGING_SECTION: {
                    TAGGING_LOCATION_KEY: "test"
                }
            }
        )

        read_config_with_parsed_config(mock_data)


class TestPrependFilepaths(unittest.TestCase):
    def _mock_json(self):
        json_str_fixture = """
        {
            "frames": {
                "st1012.png": [
                    {
                    }
                ],
                "st1013.png": [
                    {
                    }
                ],
                "st1014.png": [
                    {
                    }
                ]
            },
            "visitedFrames": [
            ]
        }
        """

        return json.loads(json_str_fixture)

    def test_correct_number_of_paths(self):
        json_resp = self._mock_json()

        data_path = pathlib.Path('/data')
        prepended_json = prepend_file_paths(data_path, json_resp)

        self.assertEqual(3, len(prepended_json['frames']))

    def test_correct_paths(self):
        json_resp = self._mock_json()

        data_path = pathlib.Path('/data')
        expected = ['/data/st1012.png', '/data/st1013.png', '/data/st1014.png']
        prepended_json = prepend_file_paths(data_path, json_resp)

        for key in prepended_json['frames'].keys():
            self.assertIn(key, expected)

    def test_deep_copy(self):
        json_resp = self._mock_json()
        data_path = pathlib.Path('/data')

        prepended_json = prepend_file_paths(data_path, json_resp)
        self.assertNotEqual(id(json_resp), id(prepended_json))


class TestTrimFilepaths(unittest.TestCase):
    def _mock_json(self):
        json_str_fixture = """
        {
            "frames": {
                "/data/st1012.png": [
                    {
                    }
                ],
                "/data/st1013.png": [
                    {
                    }
                ],
                "/data/st1014.png": [
                    {
                    }
                ]
            },
            "visitedFrames": [
                "/data/st1012.png",
                "/data/st1013.png",
                "/data/st1014.png"
            ]
        }
        """

        return json.loads(json_str_fixture)

    def test_trimmed_paths(self):
        json_resp = self._mock_json()

        expected = ['st1012.png', 'st1013.png', 'st1014.png']
        munged_json = trim_file_paths(json_resp)

        for frame_key in munged_json['frames'].keys():
            self.assertIn(frame_key, expected)

        for frame in munged_json['visitedFrames']:
            self.assertIn(frame, expected)

    def test_correct_number_of_paths(self):
        json_resp = self._mock_json()
        munged_json = trim_file_paths(json_resp)

        self.assertEqual(3, len(munged_json['frames']))
        self.assertEqual(3, len(munged_json['visitedFrames']))

    def test_deep_copy(self):
        json_resp = self._mock_json()
        munged_json = trim_file_paths(json_resp)
        self.assertNotEqual(id(json_resp), id(munged_json))


if __name__ == '__main__':
    unittest.main()
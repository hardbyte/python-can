#!/usr/bin/env python
# coding: utf-8
import shutil
import tempfile
import unittest
from tempfile import NamedTemporaryFile

import can


class LoadFileConfigTest(unittest.TestCase):
    configuration = {
        'default': {'interface': 'virtual', 'channel': '0'},
        'one': {'interface': 'virtual', 'channel': '1'},
        'two': {'channel': '2'},
        'three': {'extra': 'extra value'},
    }

    def setUp(self):
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Remove the directory after the test
        shutil.rmtree(self.test_dir)

    def _gen_configration_file(self, sections):
        with NamedTemporaryFile(mode='w', dir=self.test_dir,
                                delete=False) as tmp_config_file:
            content = []
            for section in sections:
                content.append("[{}]".format(section))
                for k, v in self.configuration[section].items():
                    content.append("{} = {}".format(k, v))
            tmp_config_file.write('\n'.join(content))
            return tmp_config_file.name

    def test_config_file_with_default(self):
        tmp_config = self._gen_configration_file(['default'])
        config = can.util.load_file_config(path=tmp_config)
        self.assertEqual(config, self.configuration['default'])

    def test_config_file_with_default_and_section(self):
        tmp_config = self._gen_configration_file(['default', 'one'])

        default = can.util.load_file_config(path=tmp_config)
        self.assertEqual(default, self.configuration['default'])

        one = can.util.load_file_config(path=tmp_config, section='one')
        self.assertEqual(one, self.configuration['one'])

    def test_config_file_with_section_only(self):
        tmp_config = self._gen_configration_file(['one'])
        config = can.util.load_file_config(path=tmp_config, section='one')
        self.assertEqual(config, self.configuration['one'])

    def test_config_file_with_section_and_key_in_default(self):
        expected = self.configuration['default'].copy()
        expected.update(self.configuration['two'])

        tmp_config = self._gen_configration_file(['default', 'two'])
        config = can.util.load_file_config(path=tmp_config, section='two')
        self.assertEqual(config, expected)

    def test_config_file_with_section_missing_interface(self):
        expected = self.configuration['two'].copy()
        tmp_config = self._gen_configration_file(['two'])
        config = can.util.load_file_config(path=tmp_config, section='two')
        self.assertEqual(config, expected)

    def test_config_file_extra(self):
        expected = self.configuration['default'].copy()
        expected.update(self.configuration['three'])

        tmp_config = self._gen_configration_file(['default', 'three'])
        config = can.util.load_file_config(path=tmp_config, section='three')
        self.assertEqual(config, expected)

    def test_config_file_with_non_existing_section(self):
        expected = {}

        tmp_config = self._gen_configration_file([
            'default', 'one', 'two', 'three'])
        config = can.util.load_file_config(path=tmp_config, section='zero')
        self.assertEqual(config, expected)


if __name__ == '__main__':
    unittest.main()

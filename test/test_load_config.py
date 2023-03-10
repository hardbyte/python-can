#!/usr/bin/env python

import shutil
import tempfile
import unittest
import unittest.mock
from tempfile import NamedTemporaryFile

import can


class LoadConfigTest(unittest.TestCase):
    configuration_in = {
        "default": {"interface": "serial", "channel": "0"},
        "one": {"interface": "kvaser", "channel": "1", "bitrate": 100000},
        "two": {"channel": "2"},
    }
    configuration_out = {
        "default": {"interface": "serial", "channel": 0},
        "one": {"interface": "kvaser", "channel": 1, "bitrate": 100000},
        "two": {"channel": 2},
    }

    def setUp(self):
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Remove the directory after the test
        shutil.rmtree(self.test_dir)

    def _gen_configration_file(self, sections):
        with NamedTemporaryFile(
            mode="w", dir=self.test_dir, delete=False
        ) as tmp_config_file:
            content = []
            for section in sections:
                content.append(f"[{section}]")
                for k, v in self.configuration_in[section].items():
                    content.append(f"{k} = {v}")
            tmp_config_file.write("\n".join(content))
            return tmp_config_file.name

    def _dict_to_env(self, d):
        return {f"CAN_{k.upper()}": str(v) for k, v in d.items()}

    def test_config_default(self):
        tmp_config = self._gen_configration_file(["default"])
        config = can.util.load_config(path=tmp_config)
        self.assertEqual(config, self.configuration_out["default"])

    def test_config_whole_default(self):
        tmp_config = self._gen_configration_file(self.configuration_in)
        config = can.util.load_config(path=tmp_config)
        self.assertEqual(config, self.configuration_out["default"])

    def test_config_whole_context(self):
        tmp_config = self._gen_configration_file(self.configuration_in)
        config = can.util.load_config(path=tmp_config, context="one")
        self.assertEqual(config, self.configuration_out["one"])

    def test_config_merge_context(self):
        tmp_config = self._gen_configration_file(self.configuration_in)
        config = can.util.load_config(path=tmp_config, context="two")
        expected = self.configuration_out["default"].copy()
        expected.update(self.configuration_out["two"])
        self.assertEqual(config, expected)

    def test_config_merge_environment_to_context(self):
        tmp_config = self._gen_configration_file(self.configuration_in)
        env_data = {"interface": "serial", "bitrate": 125000}
        env_dict = self._dict_to_env(env_data)
        with unittest.mock.patch.dict("os.environ", env_dict):
            config = can.util.load_config(path=tmp_config, context="one")
        expected = self.configuration_out["one"].copy()
        expected.update(env_data)
        self.assertEqual(config, expected)

    def test_config_whole_environment(self):
        tmp_config = self._gen_configration_file(self.configuration_in)
        env_data = {"interface": "socketcan", "channel": "3", "bitrate": 250000}
        env_dict = self._dict_to_env(env_data)
        with unittest.mock.patch.dict("os.environ", env_dict):
            config = can.util.load_config(path=tmp_config, context="one")
        expected = self.configuration_out["one"].copy()
        expected.update({"interface": "socketcan", "channel": 3, "bitrate": 250000})
        self.assertEqual(config, expected)


if __name__ == "__main__":
    unittest.main()

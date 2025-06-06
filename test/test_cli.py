import argparse
import unittest
from unittest.mock import patch

from can.cli import add_bus_arguments, create_bus_from_namespace


class TestCliUtils(unittest.TestCase):
    def test_add_bus_arguments(self):
        parser = argparse.ArgumentParser()
        add_bus_arguments(parser, filter_arg=True, prefix="test")

        parsed_args = parser.parse_args(
            [
                "--test-channel",
                "0",
                "--test-interface",
                "vector",
                "--test-timing",
                "f_clock=8000000",
                "brp=4",
                "tseg1=11",
                "tseg2=4",
                "sjw=2",
                "nof_samples=3",
                "--test-filter",
                "100:7FF",
                "200~7F0",
                "--test-bus-kwargs",
                "app_name=MyApp",
                "serial=1234",
            ]
        )

        self.assertNotIn("channel", parsed_args)
        self.assertNotIn("test_bitrate", parsed_args)
        self.assertNotIn("test_data_bitrate", parsed_args)
        self.assertNotIn("test_fd", parsed_args)

        self.assertEqual(parsed_args.test_channel, "0")
        self.assertEqual(parsed_args.test_interface, "vector")
        self.assertEqual(parsed_args.test_timing.f_clock, 8000000)
        self.assertEqual(parsed_args.test_timing.brp, 4)
        self.assertEqual(parsed_args.test_timing.tseg1, 11)
        self.assertEqual(parsed_args.test_timing.tseg2, 4)
        self.assertEqual(parsed_args.test_timing.sjw, 2)
        self.assertEqual(parsed_args.test_timing.nof_samples, 3)
        self.assertEqual(len(parsed_args.test_can_filters), 2)
        self.assertEqual(parsed_args.test_can_filters[0]["can_id"], 0x100)
        self.assertEqual(parsed_args.test_can_filters[0]["can_mask"], 0x7FF)
        self.assertEqual(parsed_args.test_can_filters[1]["can_id"], 0x200 | 0x20000000)
        self.assertEqual(
            parsed_args.test_can_filters[1]["can_mask"], 0x7F0 & 0x20000000
        )
        self.assertEqual(parsed_args.test_bus_kwargs["app_name"], "MyApp")
        self.assertEqual(parsed_args.test_bus_kwargs["serial"], 1234)

    def test_add_bus_arguments_no_prefix(self):
        parser = argparse.ArgumentParser()
        add_bus_arguments(parser, filter_arg=True)

        parsed_args = parser.parse_args(
            [
                "--channel",
                "0",
                "--interface",
                "vector",
                "--timing",
                "f_clock=8000000",
                "brp=4",
                "tseg1=11",
                "tseg2=4",
                "sjw=2",
                "nof_samples=3",
                "--filter",
                "100:7FF",
                "200~7F0",
                "--bus-kwargs",
                "app_name=MyApp",
                "serial=1234",
            ]
        )

        self.assertEqual(parsed_args.channel, "0")
        self.assertEqual(parsed_args.interface, "vector")
        self.assertEqual(parsed_args.timing.f_clock, 8000000)
        self.assertEqual(parsed_args.timing.brp, 4)
        self.assertEqual(parsed_args.timing.tseg1, 11)
        self.assertEqual(parsed_args.timing.tseg2, 4)
        self.assertEqual(parsed_args.timing.sjw, 2)
        self.assertEqual(parsed_args.timing.nof_samples, 3)
        self.assertEqual(len(parsed_args.can_filters), 2)
        self.assertEqual(parsed_args.can_filters[0]["can_id"], 0x100)
        self.assertEqual(parsed_args.can_filters[0]["can_mask"], 0x7FF)
        self.assertEqual(parsed_args.can_filters[1]["can_id"], 0x200 | 0x20000000)
        self.assertEqual(parsed_args.can_filters[1]["can_mask"], 0x7F0 & 0x20000000)
        self.assertEqual(parsed_args.bus_kwargs["app_name"], "MyApp")
        self.assertEqual(parsed_args.bus_kwargs["serial"], 1234)

    @patch("can.Bus")
    def test_create_bus_from_namespace(self, mock_bus):
        namespace = argparse.Namespace(
            test_channel="vcan0",
            test_interface="virtual",
            test_bitrate=500000,
            test_data_bitrate=2000000,
            test_fd=True,
            test_can_filters=[{"can_id": 0x100, "can_mask": 0x7FF}],
            test_bus_kwargs={"app_name": "MyApp", "serial": 1234},
        )

        create_bus_from_namespace(namespace, prefix="test")

        mock_bus.assert_called_once_with(
            channel="vcan0",
            interface="virtual",
            bitrate=500000,
            data_bitrate=2000000,
            fd=True,
            can_filters=[{"can_id": 0x100, "can_mask": 0x7FF}],
            app_name="MyApp",
            serial=1234,
            single_handle=True,
        )

    @patch("can.Bus")
    def test_create_bus_from_namespace_no_prefix(self, mock_bus):
        namespace = argparse.Namespace(
            channel="vcan0",
            interface="virtual",
            bitrate=500000,
            data_bitrate=2000000,
            fd=True,
            can_filters=[{"can_id": 0x100, "can_mask": 0x7FF}],
            bus_kwargs={"app_name": "MyApp", "serial": 1234},
        )

        create_bus_from_namespace(namespace)

        mock_bus.assert_called_once_with(
            channel="vcan0",
            interface="virtual",
            bitrate=500000,
            data_bitrate=2000000,
            fd=True,
            can_filters=[{"can_id": 0x100, "can_mask": 0x7FF}],
            app_name="MyApp",
            serial=1234,
            single_handle=True,
        )


if __name__ == "__main__":
    unittest.main()

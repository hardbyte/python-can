#!/usr/bin/env python

"""
Unittest for ixxat interface using fd option.

Run only this test:
python setup.py test --addopts "--verbose -s test/test_interface_ixxat_fd.py"
"""

import unittest
import can


class SoftwareTestCase(unittest.TestCase):
    """
    Test cases that test the software only and do not rely on an existing/connected hardware.
    """

    def setUp(self):
        try:
            bus = can.Bus(interface="ixxat", fd=True, channel=0)
            bus.shutdown()
        except can.CanInterfaceNotImplementedError:
            raise unittest.SkipTest("not available on this platform")

    def test_bus_creation(self):
        # channel must be >= 0
        with self.assertRaises(ValueError):
            can.Bus(interface="ixxat", fd=True, channel=-1)

        # rx_fifo_size must be > 0
        with self.assertRaises(ValueError):
            can.Bus(interface="ixxat", fd=True, channel=0, rx_fifo_size=0)

        # tx_fifo_size must be > 0
        with self.assertRaises(ValueError):
            can.Bus(interface="ixxat", fd=True, channel=0, tx_fifo_size=0)


class HardwareTestCase(unittest.TestCase):
    """
    Test cases that rely on an existing/connected hardware.
    """

    def setUp(self):
        try:
            bus = can.Bus(interface="ixxat", fd=True, channel=0)
            bus.shutdown()
        except can.CanInterfaceNotImplementedError:
            raise unittest.SkipTest("not available on this platform")

    def test_bus_creation(self):
        # non-existent channel -> use arbitrary high value
        with self.assertRaises(can.CanInitializationError):
            can.Bus(interface="ixxat", fd=True, channel=0xFFFF)

    def test_send_after_shutdown(self):
        with can.Bus(interface="ixxat", fd=True, channel=0) as bus:
            with self.assertRaises(can.CanOperationError):
                bus.send(can.Message(arbitration_id=0x3FF, dlc=0))


if __name__ == "__main__":
    unittest.main()

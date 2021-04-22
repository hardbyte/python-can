"""
Unittest for ixxat interface.

Run only this test:
python setup.py test --addopts "--verbose -s test/test_interface_ixxat.py"
"""

import unittest
import can


class SoftwareTestCase(unittest.TestCase):
    """
    Test cases that test the software only and do not rely on an existing/connected hardware.
    """

    def setUp(self):
        try:
            bus = can.Bus(interface="ixxat", channel=0)
            bus.shutdown()
        except ImportError:
            raise (unittest.SkipTest())

    def tearDown(self):
        pass

    def test_bus_creation(self):
        # channel must be >= 0
        with self.assertRaises(ValueError):
            bus = can.Bus(interface="ixxat", channel=-1)

        # rxFifoSize must be > 0
        with self.assertRaises(ValueError):
            bus = can.Bus(interface="ixxat", channel=0, rxFifoSize=0)

        # txFifoSize must be > 0
        with self.assertRaises(ValueError):
            bus = can.Bus(interface="ixxat", channel=0, txFifoSize=0)


class HardwareTestCase(unittest.TestCase):
    """
    Test cases that rely on an existing/connected hardware.
    """

    def setUp(self):
        try:
            bus = can.Bus(interface="ixxat", channel=0)
            bus.shutdown()
        except ImportError:
            raise (unittest.SkipTest())

    def tearDown(self):
        pass

    def test_bus_creation(self):
        # non-existent channel -> use arbitrary high value
        with self.assertRaises(can.CanInitializationError):
            bus = can.Bus(interface="ixxat", channel=0xFFFF)

    def test_send_after_shutdown(self):
        bus = can.Bus(interface="ixxat", channel=0)
        msg = can.Message(arbitration_id=0x3FF, dlc=0)
        bus.shutdown()
        with self.assertRaises(can.CanOperationError):
            bus.send(msg)


if __name__ == "__main__":
    unittest.main()

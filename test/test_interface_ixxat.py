"""
Unittest for ixxat interface.

Copyright (c) 2020, 2021 Marcel Kanter <marcel.kanter@googlemail.com>
"""

import unittest
import can
import sys

from can.interfaces.ixxat import IXXATBus


class SoftwareTestCase(unittest.TestCase):
    """
    Test cases that test the software only and do not rely on an existing/connected hardware.
    """

    def setUp(self):
        if sys.platform != "win32" and sys.platform != "cygwin":
            raise unittest.SkipTest("not available on this platform")

    def test_bus_creation(self):
        # channel must be >= 0
        with self.assertRaises(ValueError):
            can.Bus(interface="ixxat", channel=-1)

        # rxFifoSize must be > 0
        with self.assertRaises(ValueError):
            can.Bus(interface="ixxat", channel=0, rxFifoSize=0)

        # txFifoSize must be > 0
        with self.assertRaises(ValueError):
            can.Bus(interface="ixxat", channel=0, txFifoSize=0)

        # non-existent channel (use arbitrary high value)
        with self.assertRaises(can.CanInitializationError):
            can.Bus(interface="ixxat", channel=0xFFFF)

    def test_adapter_enumeration(self):
        # Enumeration of adapters should always work and the result should support len and be iterable
        adapters = IXXATBus.list_adapters()
        n = 0
        for adapter in adapters:
            n += 1
        self.assertEqual(len(adapters), n)


class HardwareTestCase(unittest.TestCase):
    """
    Test cases that rely on an existing/connected hardware.
    THEY NEED TO BE EXECUTED WITH AT LEAST ONE CONNECTED ADAPTER!
    """

    def setUp(self):
        if sys.platform != "win32" and sys.platform != "cygwin":
            raise unittest.SkipTest("not available on this platform")

    def test_bus_creation(self):
        # Test the enumeration of all adapters by opening and closing each adapter
        adapters = IXXATBus.list_adapters()
        for adapter in adapters:
            bus = can.Bus(interface="ixxat", adapter=adapter)
            bus.shutdown()

    def test_send_after_shutdown(self):
        # At least one adapter is needed, skip the test if none can be found
        adapters = IXXATBus.list_adapters()
        if len(adapters) == 0:
            raise unittest.SkipTest("No adapters found")

        bus = can.Bus(interface="ixxat", channel=0)
        msg = can.Message(arbitration_id=0x3FF, dlc=0)
        # Intentionally close the bus now and try to send afterwards. This should lead to an Exception
        bus.shutdown()
        with self.assertRaises(can.CanOperationError):
            bus.send(msg)


if __name__ == "__main__":
    unittest.main()

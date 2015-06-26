#!/usr/bin/env python3
"""
Mocks ctypes and checks that the correct low level calls are made.
"""

import ctypes

import unittest

from mock import patch, MagicMock, Mock


class KvaserTest(unittest.TestCase):

    def test_bus_creation(self):

        with patch.dict('sys.modules', ctypes=ctypes):
            import can
            can.rc['interface'] = 'kvaser'
            from can.interfaces import kvaser as interface
            from can.interfaces.kvaser import canlib

            canlib.canGetNumberOfChannels = Mock(return_value=1)
            canlib.canOpenChannel = Mock(return_value=0)
            canlib.canIoCtl = Mock(return_value=0)
            canlib.canSetBusParams = Mock()
            canlib.canBusOn = Mock()
            canlib.canSetBusOutputControl = Mock()
            canlib.canWriteWait = Mock()

            b = can.interface.Bus(channel=0, bustype='kvaser')
            assert isinstance(b, canlib.KvaserBus)
            canlib.canGetNumberOfChannels.assert_called_once()
            canlib.canBusOn.assert_called_once()

            msg = interface.Message(
                arbitration_id=0xc0ffee,
                data=[0, 25, 0, 1, 3, 1, 4, 1],
                extended_id=False)

            b.send(msg)

            canlib.canWriteWait.assert_called_once()


if __name__ == '__main__':
    unittest.main()

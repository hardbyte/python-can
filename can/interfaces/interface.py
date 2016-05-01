import can
from can.util import load_config, choose_socketcan_implementation
from can.broadcastmanager import CyclicSendTaskABC, MultiRateCyclicSendTaskABC

VALID_INTERFACES = set(['kvaser', 'serial', 'pcan', 'socketcan_native',
                                'socketcan_ctypes', 'socketcan', 'usb2can'])


class Bus(object):
    """
    Instantiates a CAN Bus of the given `bustype`, falls back to reading a
    configuration file from default locations.
    """

    @classmethod
    def __new__(cls, other, channel=None, *args, **kwargs):

        if 'bustype' in kwargs:
            can.rc['interface'] = kwargs['bustype']
            del kwargs['bustype']

            if can.rc['interface'] == 'socketcan':
                can.rc['interface'] = choose_socketcan_implementation()

        if 'interface' not in can.rc or 'channel' not in can.rc or can.rc['interface'] is None:
            can.log.debug("Loading default configuration")
            # Load defaults
            can.rc = load_config()

        if can.rc['interface'] not in VALID_INTERFACES:
            raise NotImplementedError('Invalid CAN Bus Type - {}'.format(can.rc['interface']))

        # Import the correct Bus backend
        if can.rc['interface'] == 'kvaser':
            from can.interfaces.kvaser import KvaserBus
            cls = KvaserBus
        elif can.rc['interface'] == 'socketcan_ctypes':
            from can.interfaces.socketcan_ctypes import SocketscanCtypes_Bus
            cls = SocketscanCtypes_Bus
        elif can.rc['interface'] == 'socketcan_native':
            from can.interfaces.socketcan_native import SocketscanNative_Bus
            cls = SocketscanNative_Bus
        elif can.rc['interface'] == 'serial':
            from can.interfaces.serial_can import SerialBus
            cls = SerialBus
        elif can.rc['interface'] == 'pcan':
            from can.interfaces.pcan import PcanBus
            cls = PcanBus
        elif can.rc['interface'] == 'usb2can':
            from can.interfaces.usb2canInterface import Usb2canBus
            cls = Usb2canBus
        else:
            raise NotImplementedError("CAN Interface Not Found")

        if channel is None:
            channel = can.rc['channel']
        return cls(channel, **kwargs)


class CyclicSendTask(CyclicSendTaskABC):

    @classmethod
    def __new__(cls, other, channel, *args, **kwargs):

        # If can.rc doesn't look valid: load default
        if 'interface' not in can.rc or 'channel' not in can.rc:
            can.log.debug("Loading default configuration")
            can.rc = load_config()

        print(can.rc)
        if can.rc['interface'] not in VALID_INTERFACES:
            raise NotImplementedError('Invalid CAN Bus Type - {}'.format(can.rc['interface']))

        # Import the correct implementation of CyclicSendTask
        if can.rc['interface'] == 'socketcan_ctypes':
            from can.interfaces.socketcan_ctypes import CyclicSendTask as _ctypesCyclicSendTask
            cls = _ctypesCyclicSendTask
        elif can.rc['interface'] == 'socketcan_native':
            from can.interfaces.socketcan_native import CyclicSendTask as _nativeCyclicSendTask
            cls = _nativeCyclicSendTask
        else:
            can.log.info("Current CAN interface doesn't support CyclicSendTask")

        return cls(channel, *args, **kwargs)


class MultiRateCyclicSendTask(MultiRateCyclicSendTaskABC):

    @classmethod
    def __new__(cls, other, channel, *args, **kwargs):

        # If can.rc doesn't look valid: load default
        if 'interface' not in can.rc or 'channel' not in can.rc:
            can.log.debug("Loading default configuration")
            can.rc = load_config()

        print(can.rc)
        if can.rc['interface'] not in VALID_INTERFACES:
            raise NotImplementedError('Invalid CAN Bus Type - {}'.format(can.rc['interface']))

        # Import the correct implementation of CyclicSendTask
        if can.rc['interface'] == 'socketcan_ctypes':
            from can.interfaces.socketcan_ctypes import MultiRateCyclicSendTask as _ctypesMultiRateCyclicSendTask
            cls = _ctypesMultiRateCyclicSendTask
        elif can.rc['interface'] == 'socketcan_native':
            from can.interfaces.socketcan_native import MultiRateCyclicSendTask as _nativeMultiRateCyclicSendTask
            cls = _nativeMultiRateCyclicSendTask
        else:
            can.log.info("Current CAN interface doesn't support CyclicSendTask")

        return cls(channel, *args, **kwargs)

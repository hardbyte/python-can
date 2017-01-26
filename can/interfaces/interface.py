import can
from can.broadcastmanager import CyclicSendTaskABC, MultiRateCyclicSendTaskABC
from can.util import load_config, choose_socketcan_implementation

VALID_INTERFACES = set(['kvaser', 'serial', 'pcan', 'socketcan_native',
                        'socketcan_ctypes', 'socketcan', 'usb2can', 'ixxat',
                        'nican', 'remote', 'virtual'])


class Bus(object):
    """
    Instantiates a CAN Bus of the given `bustype`, falls back to reading a
    configuration file from default locations.
    """

    @classmethod
    def __new__(cls, other, channel=None, *args, **kwargs):
        """
        Takes the same arguments as :class:`can.BusABC` with the addition of:

        :param kwargs:
            Should contain a bustype key with a valid interface name.

        :raises: NotImplementedError if the bustype isn't recognized
        """
        if 'bustype' in kwargs:
            can.rc['interface'] = kwargs['bustype']
            del kwargs['bustype']

            if can.rc['interface'] == 'socketcan':
                can.rc['interface'] = choose_socketcan_implementation()

        # Update can.rc from kwargs
        for kw in ('interface', 'bitrate'):
            if kw in kwargs:
                can.rc[kw] = kwargs[kw]

        if 'interface' not in can.rc or 'channel' not in can.rc or can.rc['interface'] is None:
            can.log.debug("Loading default configuration")
            # Load defaults
            can.rc = load_config()

        if can.rc['interface'] not in VALID_INTERFACES:
            raise NotImplementedError('Invalid CAN Bus Type - {}'.format(can.rc['interface']))

        # Import the correct Bus backend
        interface = can.rc['interface']
        if interface == 'kvaser':
            from can.interfaces.kvaser import KvaserBus
            cls = KvaserBus
        elif interface == 'socketcan_ctypes':
            from can.interfaces.socketcan import SocketcanCtypes_Bus
            cls = SocketcanCtypes_Bus
        elif interface == 'socketcan_native':
            from can.interfaces.socketcan import SocketcanNative_Bus
            cls = SocketcanNative_Bus
        elif interface == 'serial':
            from can.interfaces.serial.serial_can import SerialBus
            cls = SerialBus
        elif interface == 'pcan':
            from can.interfaces.pcan import PcanBus
            cls = PcanBus
        elif interface == 'usb2can':
            from can.interfaces.usb2can import Usb2canBus
            cls = Usb2canBus
        elif interface == 'ixxat':
            from can.interfaces.ixxat import IXXATBus
            cls = IXXATBus
        elif interface == 'nican':
            from can.interfaces.nican import NicanBus
            cls = NicanBus
        elif interface == 'remote':
            from can.interfaces.remote import RemoteBus
            cls = RemoteBus
        elif interface == 'virtual':
            from can.interfaces.virtual import VirtualBus
            cls = VirtualBus
        else:
            raise NotImplementedError("CAN interface '{}' not supported".format(interface))

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
            from can.interfaces.socketcan.socketcan_ctypes import CyclicSendTask as _ctypesCyclicSendTask
            cls = _ctypesCyclicSendTask
        elif can.rc['interface'] == 'socketcan_native':
            from can.interfaces.socketcan.socketcan_native import CyclicSendTask as _nativeCyclicSendTask
            cls = _nativeCyclicSendTask
        # CyclicSendTask has not been fully implemented on remote interface yet.
        # Waiting for issue #80 which will change the API to make it easier for
        # interfaces other than socketcan to implement it
        #elif can.rc['interface'] == 'remote':
        #    from can.interfaces.remote import CyclicSendTask as _remoteCyclicSendTask
        #    cls = _remoteCyclicSendTask
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
            from can.interfaces.socketcan.socketcan_ctypes import MultiRateCyclicSendTask as _ctypesMultiRateCyclicSendTask
            cls = _ctypesMultiRateCyclicSendTask
        elif can.rc['interface'] == 'socketcan_native':
            from can.interfaces.socketcan.socketcan_native import MultiRateCyclicSendTask as _nativeMultiRateCyclicSendTask
            cls = _nativeMultiRateCyclicSendTask
        else:
            can.log.info("Current CAN interface doesn't support CyclicSendTask")

        return cls(channel, *args, **kwargs)

import can
from can.broadcastmanager import CyclicSendTaskABC, MultiRateCyclicSendTaskABC
from can.util import load_config


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

        :raises:
            NotImplementedError if the bustype isn't recognized
        :raises:
            ValueError if the bustype or channel isn't either passed as an argument
            or set in the can.rc config.

        """
        config = load_config(config={
            'interface': kwargs.get('bustype'),
            'channel': channel
        })

        if 'bustype' in kwargs:
            # remove the bustype so it doesn't get passed to the backend
            del kwargs['bustype']
        interface = config['interface']
        channel = config['channel']

        # Import the correct Bus backend
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
        elif interface == 'neovi':
            from can.interfaces.neovi_api import NeoVIBus
            cls = NeoVIBus
        else:
            raise NotImplementedError("CAN interface '{}' not supported".format(interface))

        return cls(channel, **kwargs)


class CyclicSendTask(CyclicSendTaskABC):

    @classmethod
    def __new__(cls, other, channel, *args, **kwargs):

        config = load_config(config={'channel': channel})

        # Import the correct implementation of CyclicSendTask
        if config['interface'] == 'socketcan_ctypes':
            from can.interfaces.socketcan.socketcan_ctypes import CyclicSendTask as _ctypesCyclicSendTask
            cls = _ctypesCyclicSendTask
        elif config['interface'] == 'socketcan_native':
            from can.interfaces.socketcan.socketcan_native import CyclicSendTask as _nativeCyclicSendTask
            cls = _nativeCyclicSendTask
        # CyclicSendTask has not been fully implemented on remote interface yet.
        # Waiting for issue #80 which will change the API to make it easier for
        # interfaces other than socketcan to implement it
        #elif can.rc['interface'] == 'remote':
        #    from can.interfaces.remote import CyclicSendTask as _remoteCyclicSendTask
        #    cls = _remoteCyclicSendTask
        else:
            raise can.CanError("Current CAN interface doesn't support CyclicSendTask")

        return cls(config['channel'], *args, **kwargs)


class MultiRateCyclicSendTask(MultiRateCyclicSendTaskABC):

    @classmethod
    def __new__(cls, other, channel, *args, **kwargs):

        config = load_config(config={'channel': channel})

        # Import the correct implementation of CyclicSendTask
        if config['interface'] == 'socketcan_ctypes':
            from can.interfaces.socketcan.socketcan_ctypes import MultiRateCyclicSendTask as _ctypesMultiRateCyclicSendTask
            cls = _ctypesMultiRateCyclicSendTask
        elif config['interface'] == 'socketcan_native':
            from can.interfaces.socketcan.socketcan_native import MultiRateCyclicSendTask as _nativeMultiRateCyclicSendTask
            cls = _nativeMultiRateCyclicSendTask
        else:
            can.log.info("Current CAN interface doesn't support CyclicSendTask")

        return cls(config['channel'], *args, **kwargs)

import can
from can.util import load_config


class Bus(object):
    """
    Instantiates a CAN Bus of the given `bustype`, falls back to reading a
    configuration file from default locations.
    """

    @classmethod
    def __new__(cls, other, channel, *args, **kwargs):
        if 'bustype' in kwargs:
            if kwargs['bustype'] == 'kvaser':
                can.rc['interface'] = 'kvaser'
            elif kwargs['bustype'] == 'socketcan_ctypes':
                can.rc['interface'] = 'socketcan_ctypes'
            elif kwargs['bustype'] == 'socketcan_native':
                can.rc['interface'] = 'socketcan_native'
            elif kwargs['bustype'] == 'socketcan':
                try:
                    import fcntl
                    can.rc['interface'] = 'socketcan_native'
                except ImportError:
                    can.rc['interface'] = 'socketcan_ctypes'
            elif kwargs['bustype'] == 'serial':
                can.rc['interface'] = 'serial'
            elif kwargs['bustype'] == 'pcan':
                can.rc['interface'] = 'pcan'
            else:
                raise NotImplementedError('Invalid CAN Bus Type.')
            del kwargs['bustype']
        else:
            can.rc = load_config()

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
        else:
            raise NotImplementedError("CAN Interface Not Found")

        return cls(channel, **kwargs)

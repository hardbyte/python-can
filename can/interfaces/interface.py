import can
from can.util import load_config

from can.interfaces.kvaser import *
from can.interfaces.serial_can import *
from can.interfaces.pcan import *
try:
    from can.interfaces.socketcan_native import *
except ImportError:
    from can.interfaces.socketcan_ctypes import *


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
                cls = KvaserBus
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
            elif kwargs['bustype'] =='serial':
                can.rc['interface'] = 'serial'
                cls = SerialBus
            elif kwargs['bustype'] =='pcan':
                can.rc['interface'] = 'pcan'
                cls = PcanBus
            else:
                raise NotImplementedError('Invalid CAN Bus Type.')
            del kwargs['bustype']
        else:
            can.rc = load_config()

        if can.rc['interface'] == 'kvaser':
            cls = KvaserBus
        elif can.rc['interface'] == 'socketcan_ctypes':
            cls = SocketscanCtypes_Bus
        elif can.rc['interface'] == 'socketcan_native':
            cls = SocketscanNative_Bus
        elif can.rc['interface'] =='serial':
            cls = SerialBus
        elif can.rc['interface'] =='pcan':
            cls = PcanBus
        else:
            raise NotImplementedError("CAN Interface Not Found")

        return cls(channel, **kwargs)


import can
from can.util import load_config

from can.interfaces.kvaser import *
from can.interfaces.serial_can import *
from can.interfaces.pcan import *
try:
    from can.interfaces.socketcan_native import *
except ImportError:
    from can.interfaces.socketcan_ctypes import *

''' This will only read the configuration file if used in the old style of initialization,
    otherwise it uses the bustype keyword arguement to specify the type of can bus.  
'''
class Bus(object):
    @classmethod
    def __new__(cls, *args, **kwargs):
        print cls
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

        print cls
        return cls(*args, **kwargs)


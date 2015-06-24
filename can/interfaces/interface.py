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
                # Check OS: SocketCAN is available only under Linux
                import sys
                if sys.platform.startswith('linux'):
                    # Check release: SocketCAN was added to Linux 2.6.25
                    import platform
                    import re
                    rel_string = platform.release()
                    m = re.match('\d+\.\d+\.\d', rel_string)
                    if m is None:
                        msg = 'Bad linux release {}'.format(rel_string)
                        raise Exception(msg)
                    rel_num = [int(i) for i in rel_string[:m.end()].split('.')]
                    print('rel_num {}'.format(rel_num))
                    if (rel_num >= [2, 6, 25]):
                        # Check Python version: SocketCAN was added in 3.3
                        py_ver = [sys.version_info[0], sys.version_info[1]]
                        if (py_ver >= [3, 3]):
                            print('python >= 3.3')
                            can.rc['interface'] = 'socketcan_native'
                        else:
                            print('python < 3.3')
                            can.rc['interface'] = 'socketcan_ctypes'
                    else:
                        msg = 'SocketCAN not available under Linux {}'.format(
                                rel_string)
                        raise Exception(msg)
                else:
                    msg = 'SocketCAN not available under {}'.format(
                        sys.platform)
                    raise Exception(msg)
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

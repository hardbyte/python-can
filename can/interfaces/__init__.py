# -*- coding: utf-8 -*-
"""
Interfaces contain low level implementations that interact with CAN hardware.
"""
import can

if can.rc['interface'] == 'kvaser':
    from can.interfaces.canlib import *
elif can.rc['interface'] == 'socketcan_ctypes':
    from can.interfaces.socketcan_ctypes import *
elif can.rc['interface'] == 'socketcan_native':
    from can.interfaces.socketcan_native import *
elif can.rc['interface'] == 'socketcan':
    # try both
    try:
        from can.interfaces.socketcan_native import *
    except:
        from can.interfaces.socketcan_ctypes import *
else:
    raise ImportError("CAN interface not found")
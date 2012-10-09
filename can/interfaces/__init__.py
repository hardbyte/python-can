# -*- coding: utf-8 -*-
"""
Interfaces contain low level implementations that interact with CAN hardware.
"""

# TODO for now the backend is set here...
interface = 'socketcan_ctypes' # 'canlib' # or socketcan_ctypes, socketcan_native


if interface == 'canlib':
    from canlib import *
elif interface == 'socketcan_ctypes':
    from socketcan_ctypes import *
else:
    from socketcan_native import *

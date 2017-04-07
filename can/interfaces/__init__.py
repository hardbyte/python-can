# -*- coding: utf-8 -*-
"""
Interfaces contain low level implementations that interact with CAN hardware.
"""

VALID_INTERFACES = set(['kvaser', 'serial', 'pcan', 'socketcan_native',
                        'socketcan_ctypes', 'socketcan', 'usb2can', 'ixxat',
                        'nican', 'remote', 'virtual', 'neovi'])

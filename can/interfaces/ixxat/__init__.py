"""
Ctypes wrapper module for IXXAT Virtual CAN Interface V4 on win32 systems

Copyright (C) 2016-2021 Giuseppe Corbelli <giuseppe.corbelli@weightpack.com>
"""

__all__ = [
    "canlib",
    "constants",
    "CyclicSendTask"
    "exceptions",
    "get_ixxat_hwids",
    "IXXATBus",
    "structures",
]

from can.interfaces.ixxat.canlib import CyclicSendTask, get_ixxat_hwids, IXXATBus

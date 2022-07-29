"""
Ctypes wrapper module for IXXAT Virtual CAN Interface V3 on win32 systems

Copyright (C) 2016 Giuseppe Corbelli <giuseppe.corbelli@weightpack.com>
"""

from can.interfaces.ixxat.canlib import IXXATBus
from can.interfaces.ixxat.canlib_vcinpl import (
    get_ixxat_hwids,
)  # import this and not the one from vcinpl2 for backward compatibility

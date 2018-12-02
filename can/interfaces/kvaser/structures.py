# coding: utf-8

"""
Contains Python equivalents of the structures in CANLIB's canstat.h, 
with some supporting functionality specific to Python.

Copyright (C) 2010 Dynamic Controls
"""

import ctypes


class BusStatistics(ctypes.Structure):
    _fields_ = [
        ("stdData", ctypes.c_ulong),
        ("stdRemote", ctypes.c_ulong),
        ("extData", ctypes.c_ulong),
        ("extRemote", ctypes.c_ulong),
        ("errFrame", ctypes.c_ulong),
        ("busLoad", ctypes.c_ulong),
        ("overruns", ctypes.c_ulong)
    ]

    def __str__(self):
        return ("stdData: {}, stdRemote: {}, extData: {}, extRemote: {}, "
                "errFrame: {}, busLoad: {:.1f}%, overruns: {}").format(
            self.stdData,
            self.stdRemote,
            self.extData,
            self.extRemote,
            self.errFrame,
            self.busLoad / 100.0,
            self.overruns,
        )

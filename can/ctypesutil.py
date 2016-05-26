#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import binascii
import ctypes
import logging
import sys

log = logging.getLogger('can.ctypesutil')

__all__ = ['CLibrary', 'HANDLE', 'PHANDLE']


class LibraryMixin:
    def map_symbol(self, func_name, restype=None, argtypes=(), errcheck=None):
        if (argtypes):
            prototype = self.function_type(restype, *argtypes)
        else:
            prototype = self.function_type(restype)
        try:
            symbol = prototype((func_name, self))
        except AttributeError:
            raise ImportError("Could not map function '{}' from library {}".format(func_name, self._name))

        setattr(symbol, "_name", func_name)
        log.debug('Wrapped function "{}", result type: {}, error_check {}'.format(func_name, type(restype), errcheck))

        if (errcheck):
            symbol.errcheck = errcheck

        setattr(self, func_name, symbol)
        return symbol


class CLibrary_Win32(ctypes.WinDLL, LibraryMixin):
    def __init__(self, library_or_path):
        if (isinstance(library_or_path, str)):
            super().__init__(library_or_path)
        else:
            super().__init__(library_or_path._name, library_or_path._handle)

    @property
    def function_type(self):
        return ctypes.WINFUNCTYPE


class CLibrary_Unix(ctypes.CDLL, LibraryMixin):
    FUNCTYPE = ctypes.CFUNCTYPE

    def __init__(self, library_or_path):
        if (isinstance(library_or_path, str)):
            super().__init__(library_or_path)
        else:
            super().__init__(library_or_path._name, library_or_path._handle)

    @property
    def function_type(self):
        return ctypes.CFUNCTYPE


if sys.platform == "win32":
    CLibrary = CLibrary_Win32
else:
    CLibrary = CLibrary_Unix


# Common win32 definitions
class HANDLE(ctypes.c_void_p):
    pass

PHANDLE = ctypes.POINTER(HANDLE)

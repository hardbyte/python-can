# coding: utf-8

"""
This module contains common `ctypes` utils.
"""

import binascii
import ctypes
import logging
import sys

log = logging.getLogger('can.ctypesutil')

__all__ = ['CLibrary', 'HANDLE', 'PHANDLE', 'HRESULT']

try:
    _LibBase = ctypes.WinDLL
except AttributeError:
    _LibBase = ctypes.CDLL


class LibraryMixin:
    def map_symbol(self, func_name, restype=None, argtypes=(), errcheck=None):
        """
        Map and return a symbol (function) from a C library. A reference to the
        mapped symbol is also held in the instance

        :param str func_name:
            symbol_name
        :param ctypes.c_* restype:
            function result type (i.e. ctypes.c_ulong...), defaults to void
        :param tuple(ctypes.c_* ... ) argtypes:
            argument types, defaults to no args
        :param callable errcheck:
            optional error checking function, see ctypes docs for _FuncPtr
        """
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


class CLibrary_Win32(_LibBase, LibraryMixin):
    " Basic ctypes.WinDLL derived class + LibraryMixin "

    def __init__(self, library_or_path):
        if (isinstance(library_or_path, str)):
            super(CLibrary_Win32, self).__init__(library_or_path)
        else:
            super(CLibrary_Win32, self).__init__(library_or_path._name, library_or_path._handle)

    @property
    def function_type(self):
        return ctypes.WINFUNCTYPE


class CLibrary_Unix(ctypes.CDLL, LibraryMixin):
    " Basic ctypes.CDLL derived class + LibraryMixin "

    def __init__(self, library_or_path):
        if (isinstance(library_or_path, str)):
            super(CLibrary_Unix, self).__init__(library_or_path)
        else:
            super(CLibrary_Unix, self).__init__(library_or_path._name, library_or_path._handle)

    @property
    def function_type(self):
        return ctypes.CFUNCTYPE


if sys.platform == "win32":
    CLibrary = CLibrary_Win32
    HRESULT = ctypes.HRESULT
else:
    CLibrary = CLibrary_Unix
    if sys.platform == "cygwin":
        # Define HRESULT for cygwin
        class HRESULT(ctypes.c_long):
            pass


# Common win32 definitions
class HANDLE(ctypes.c_void_p):
    pass

PHANDLE = ctypes.POINTER(HANDLE)

"""
This module contains common `ctypes` utils.
"""

import ctypes
import logging
import sys

from typing import Any, Callable, Optional, Tuple, Union

log = logging.getLogger("can.ctypesutil")

__all__ = ["CLibrary", "HANDLE", "PHANDLE", "HRESULT"]


try:
    _LibBase = ctypes.WinDLL  # type: ignore
    _FUNCTION_TYPE = ctypes.WINFUNCTYPE  # type: ignore
except AttributeError:
    _LibBase = ctypes.CDLL
    _FUNCTION_TYPE = ctypes.CFUNCTYPE


class CLibrary(_LibBase):  # type: ignore
    def __init__(self, library_or_path: Union[str, ctypes.CDLL]) -> None:
        if isinstance(library_or_path, str):
            super().__init__(library_or_path)
        else:
            super().__init__(library_or_path._name, library_or_path._handle)

    def map_symbol(
        self,
        func_name: str,
        restype: Any = None,
        argtypes: Tuple[Any, ...] = (),
        errcheck: Optional[Callable[..., Any]] = None,
    ) -> Any:
        """
        Map and return a symbol (function) from a C library. A reference to the
        mapped symbol is also held in the instance

        :param func_name:
            symbol_name
        :param ctypes.c_* restype:
            function result type (i.e. ctypes.c_ulong...), defaults to void
        :param tuple(ctypes.c_* ... ) argtypes:
            argument types, defaults to no args
        :param callable errcheck:
            optional error checking function, see ctypes docs for _FuncPtr
        """
        if argtypes:
            prototype = _FUNCTION_TYPE(restype, *argtypes)
        else:
            prototype = _FUNCTION_TYPE(restype)
        try:
            symbol: Any = prototype((func_name, self))
        except AttributeError:
            raise ImportError(
                f'Could not map function "{func_name}" from library {self._name}'
            ) from None

        symbol._name = func_name
        log.debug(
            f'Wrapped function "{func_name}", result type: {type(restype)}, error_check {errcheck}'
        )

        if errcheck is not None:
            symbol.errcheck = errcheck

        self.func_name = symbol

        return symbol


if sys.platform == "win32":
    HRESULT = ctypes.HRESULT

elif sys.platform == "cygwin":

    class HRESULT(ctypes.c_long):
        pass


# Common win32 definitions
class HANDLE(ctypes.c_void_p):
    pass


PHANDLE = ctypes.POINTER(HANDLE)

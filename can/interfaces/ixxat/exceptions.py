# -*- coding: utf-8 -*-
"""
Ctypes wrapper module for IXXAT Virtual CAN Interface V3 on win32 systems
Copyright (C) 2016 Giuseppe Corbelli <giuseppe.corbelli@weightpack.com>
"""

import ctypes

from . import constants

from can import CanError

__all__ = ['VCITimeout', 'VCIError', 'VCIDeviceNotFoundError']

class VCITimeout(CanError):
    pass


class VCIError(CanError):
    " Try to display errors that occur within the wrapped C library nicely. "

    _ERROR_BUFFER = ctypes.create_string_buffer(constants.VCI_MAX_ERRSTRLEN)

    def __init__(self, function, HRESULT, arguments):
        super(VCIError, self).__init__()
        self.HRESULT = HRESULT
        self.function = function
        self.arguments = arguments

    def __str__(self):
        return "function {} failed - {} - arguments were {}".format(
            self.function.__name__,
            self.__get_error_message(),
            self.arguments
        )

    def __get_error_message(self):
        ctypes.memset(self._ERROR_BUFFER, 0, constants.VCI_MAX_ERRSTRLEN)
        vciFormatError(self.HRESULT, self._ERROR_BUFFER, constants.VCI_MAX_ERRSTRLEN)
        return "{}".format(self._ERROR_BUFFER)


class VCIDeviceNotFoundError(CanError):
    pass

# coding: utf-8

"""
Ctypes wrapper module for IXXAT Virtual CAN Interface V3 on win32 systems

Copyright (C) 2016 Giuseppe Corbelli <giuseppe.corbelli@weightpack.com>
"""

from can import CanError

__all__ = ['VCITimeout', 'VCIError', 'VCIRxQueueEmptyError', 'VCIDeviceNotFoundError']


class VCITimeout(CanError):
    """ Wraps the VCI_E_TIMEOUT error """
    pass


class VCIError(CanError):
    """ Try to display errors that occur within the wrapped C library nicely. """
    pass


class VCIRxQueueEmptyError(VCIError):
    """ Wraps the VCI_E_RXQUEUE_EMPTY error """
    def __init__(self):
        super(VCIRxQueueEmptyError, self).__init__("Receive queue is empty")


class VCIDeviceNotFoundError(CanError):
    pass

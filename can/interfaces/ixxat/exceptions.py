# coding: utf-8

"""
Ctypes wrapper module for IXXAT Virtual CAN Interface V3 on win32 systems

Copyright (C) 2016 Giuseppe Corbelli <giuseppe.corbelli@weightpack.com>
Copyright (C) 2019 Marcel Kanter <marcel.kanter@googlemail.com>
"""

from can import CanError, CanBackEndError, CanInitializationError, CanOperationError, CanTimeoutError


class VCITimeout(CanTimeoutError):
    """ Wraps the VCI_E_TIMEOUT error """
    pass


class VCIError(CanOperationError):
    """ Try to display errors that occur within the wrapped C library nicely. """
    pass


class VCIRxQueueEmptyError(VCIError):
    """ Wraps the VCI_E_RXQUEUE_EMPTY error """
    def __init__(self):
        super(VCIRxQueueEmptyError, self).__init__("Receive queue is empty")


class VCIDeviceNotFoundError(CanInitializationError):
    pass

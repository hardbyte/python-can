"""
Ctypes wrapper module for IXXAT Virtual CAN Interface V3 on win32 systems

Copyright (C) 2016 Giuseppe Corbelli <giuseppe.corbelli@weightpack.com>
"""

from ... import CanError

__all__ = [
    "VCITimeout",
    "VCIError",
    "VCIRxQueueEmptyError",
    "VCIBusOffError",
    "VCIDeviceNotFoundError",
]


class VCITimeout(CanError):
    """ Wraps the VCI_E_TIMEOUT error """


class VCIError(CanError):
    """ Try to display errors that occur within the wrapped C library nicely. """


class VCIRxQueueEmptyError(VCIError):
    """ Wraps the VCI_E_RXQUEUE_EMPTY error """

    def __init__(self):
        super().__init__("Receive queue is empty")


class VCIBusOffError(VCIError):
    def __init__(self):
        super().__init__("Controller is in BUSOFF state")


class VCIDeviceNotFoundError(CanError):
    pass

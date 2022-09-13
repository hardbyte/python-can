import ctypes
from can.ctypesutil import HANDLE

# These exist so that implementation matches the API.
DWORD = ctypes.c_uint32
DEV_SEARCH_HANDLE = HANDLE


# Note: FFMessage is not defined in the API.  Choose to make a union of
# EFFMessage and SFFMessage to make implemented EcomBus more straightforward.
class FFMessage(ctypes.Union):
    class SFFMessage(ctypes.Structure):
        _fields_ = [
            ("IDH", ctypes.c_ubyte),
            ("IDL", ctypes.c_ubyte),
            ("Data", ctypes.c_byte * 8),
            ("Options", ctypes.c_byte),
            ("DataLength", ctypes.c_byte),
            ("TimeStamp", DWORD),
        ]

    class EFFMessage(ctypes.Structure):
        _fields_ = [
            ("ID", DWORD),
            ("Data", ctypes.c_byte * 8),
            ("Options", ctypes.c_byte),
            ("DataLength", ctypes.c_byte),
            ("TimeStamp", DWORD),
        ]

    _fields_ = [("SFFMessage", SFFMessage), ("EFFMessage", EFFMessage)]


PFFMessage = ctypes.POINTER(FFMessage)


class DeviceInfo(ctypes.Structure):
    _fields_ = [
        ("SerialNumber", ctypes.c_ulong),
        ("CANOpen", ctypes.c_byte),
        ("SEROpen", ctypes.c_byte),
        ("_reserved", ctypes.c_byte),
        ("SyncCANTx", ctypes.c_byte),  # Always False.
        ("DeviceHandle", HANDLE),  # Always null.
        ("reserved", ctypes.c_byte * 10),
    ]


PDeviceInfo = ctypes.POINTER(DeviceInfo)


class ErrorMessage(ctypes.Structure):
    _fields_ = [
        ("ErrorFIFOSize", ctypes.c_uint),
        ("ErrorCode", ctypes.c_byte),
        ("Timestamp", ctypes.c_double),
        ("reserved", ctypes.c_byte * 2),
    ]


PErrorMessage = ctypes.POINTER(ErrorMessage)

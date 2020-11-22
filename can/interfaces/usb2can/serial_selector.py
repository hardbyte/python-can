"""
"""

import logging

try:
    import ctypes.wintypes
    import ctypes

    _setupapi = ctypes.windll.SetupApi
    _kernel32 = ctypes.WinDLL.Kernel32
    _ole32 = ctypes.windll.Ole32

    _BOOL = ctypes.wintypes.BOOL
    _UINT32 = ctypes.c_uint32
    _UINT16 = ctypes.c_uint16
    _UBYTE = ctypes.c_ubyte
    _PWCHAR = ctypes.c_wchar_p
    _ULONG = ctypes.wintypes.ULONG
    _LPVOID = ctypes.c_void_p
    _HDEVINFO = ctypes.wintypes.HANDLE

    INVALID_HANDLE_VALUE = -1
    DIOD_INHERIT_CLASSDRVS = 2
    DIGCF_PRESENT = 0x00000002
    DIGCF_ALLCLASSES = 0x00000004
    ERROR_NO_MORE_ITEMS = 0x00000103
    ERROR_INSUFFICIENT_BUFFER = 0x0000007A


    class GUID(ctypes.Structure):
        _fields_ = [
            ('Data1', _UINT32),
            ('Data2', _UINT16),
            ('Data3', _UINT16),
            ('Data4', _UBYTE * 8)
        ]

        def __init__(
            self,
            guid="{00000000-0000-0000-0000-000000000000}"
        ):
            super().__init__()
            ret = _ole32.CLSIDFromString(
                ctypes.create_unicode_buffer(guid),
                ctypes.byref(self)
            )
            if ret < 0:
                raise ctypes.WinError()

    class DevicePropertyKey(ctypes.Structure):
        _fields_ = [
            ('fmtid', GUID),
            ('pid', _ULONG)
        ]


    DEVPKEY_Device_InstanceId = DevicePropertyKey(
        '{78c34fc8-104a-4aca-9ea4-524d52996e57}',
        256
    )


    class _SP_DEVINFO_DATA(ctypes.Structure):
        _fields_ = [
            ('cbSize', _ULONG),
            ('ClassGuid', GUID),
            ('DevInst', _ULONG),
            ('Reserved', _LPVOID)
        ]

    _SetupDiGetClassDevsW = _setupapi.SetupDiGetClassDevsW
    _SetupDiGetClassDevsW.restype = _HDEVINFO

    _SetupDiEnumDeviceInfo = _setupapi.SetupDiEnumDeviceInfo
    _SetupDiEnumDeviceInfo.restype = _BOOL

    _SetupDiGetDevicePropertyW = _setupapi.SetupDiGetDevicePropertyW
    _SetupDiGetDevicePropertyW.restype = _BOOL

    _SetupDiDestroyDeviceInfoList = _setupapi.SetupDiDestroyDeviceInfoList
    _SetupDiDestroyDeviceInfoList.restype = _BOOL


    def devices():
        flags = DIGCF_PRESENT | DIGCF_ALLCLASSES
        enumerator = ctypes.create_unicode_buffer('USB')

        guid = GUID()
        _ole32.CLSIDFromString(
            "{A5DCBF10-6530-11D2-901F-00C04FB951ED}",
            ctypes.byref(guid)
        )

        hDevInfo = _SetupDiGetClassDevsW(
            guid,
            enumerator,
            None,
            flags
        )

        if hDevInfo == INVALID_HANDLE_VALUE:
            raise ctypes.WinError()

        deviceInfoData = _SP_DEVINFO_DATA()
        deviceInfoData.cbSize = ctypes.sizeof(_SP_DEVINFO_DATA)

        i = 0
        while True:
            if not _SetupDiEnumDeviceInfo(
                hDevInfo,
                i,
                ctypes.byref(deviceInfoData)
            ):
                err = ctypes.GetLastError()
                if err == ERROR_NO_MORE_ITEMS:
                    break
                else:
                    raise ctypes.WinError(err)
            
            i += 1

            prop_type = _ULONG()
            required_size = _ULONG()
            _SetupDiGetDevicePropertyW(
                hDevInfo,
                ctypes.byref(deviceInfoData),
                ctypes.byref(DEVPKEY_Device_InstanceId),
                ctypes.byref(prop_type),
                None,
                0,
                ctypes.byref(required_size),
                0
            )

            if required_size.value == 0:
                continue

            instance_id_buffer = ctypes.create_string_buffer(
                required_size.value
            )

            _setupapi.SetupDiGetDevicePropertyW(
                hDevInfo,
                ctypes.byref(deviceInfoData),
                ctypes.byref(DEVPKEY_Device_InstanceId),
                ctypes.byref(prop_type),
                instance_id_buffer,
                required_size.value,
                ctypes.byref(required_size),
                0
            )

            yield instance_id_buffer.value

        _SetupDiDestroyDeviceInfoList(hDevInfo)


except ImportError:
    logging.warning("unsupported operating system.")
    raise


def WMIDateStringToDate(dtmDate):
    if dtmDate[4] == 0:
        strDateTime = dtmDate[5] + "/"
    else:
        strDateTime = dtmDate[4] + dtmDate[5] + "/"

    if dtmDate[6] == 0:
        strDateTime = strDateTime + dtmDate[7] + "/"
    else:
        strDateTime = strDateTime + dtmDate[6] + dtmDate[7] + "/"
        strDateTime = (
            strDateTime
            + dtmDate[0]
            + dtmDate[1]
            + dtmDate[2]
            + dtmDate[3]
            + " "
            + dtmDate[8]
            + dtmDate[9]
            + ":"
            + dtmDate[10]
            + dtmDate[11]
            + ":"
            + dtmDate[12]
            + dtmDate[13]
        )
    return strDateTime


def find_serial_devices(serial_matcher="ED"):
    """
    Finds a list of USB devices where the serial number (partially) matches the given string.

    :param str serial_matcher (optional):
        only device IDs starting with this string are returned

    :rtype: List[str]
    """
    res = set()
    for instance_id in devices():
        instance_id = instance_id.strip('"')[-8:]
        if instance_id.startswith(serial_matcher):
            res.add(instance_id)

    return [ins_id for ins_id in res]

# coding: utf-8

"""
"""

from __future__ import division, print_function, absolute_import

import logging

try:
    import win32com.client
except ImportError:
    logging.warning("win32com.client module required for usb2can")
    raise


def WMIDateStringToDate(dtmDate):
    if (dtmDate[4] == 0):
        strDateTime = dtmDate[5] + '/'
    else:
        strDateTime = dtmDate[4] + dtmDate[5] + '/'

    if (dtmDate[6] == 0):
        strDateTime = strDateTime + dtmDate[7] + '/'
    else:
        strDateTime = strDateTime + dtmDate[6] + dtmDate[7] + '/'
        strDateTime = strDateTime + dtmDate[0] + dtmDate[1] + dtmDate[2] + dtmDate[3] + ' ' + dtmDate[8] + dtmDate[9] \
            + ':' + dtmDate[10] + dtmDate[11] + ':' + dtmDate[12] + dtmDate[13]
    return strDateTime


def find_serial_devices(serial_matcher="ED"):
    """
    Finds a list of USB devices where the serial number (partially) matches the given string.

    :param str serial_matcher (optional):
        only device IDs starting with this string are returned

    :rtype: List[str]
    """
    objWMIService = win32com.client.Dispatch("WbemScripting.SWbemLocator")
    objSWbemServices = objWMIService.ConnectServer(".", "root\cimv2")
    items = objSWbemServices.ExecQuery("SELECT * FROM Win32_USBControllerDevice")
    ids = (item.Dependent.strip('"')[-8:] for item in items)
    return [e for e in ids if e.startswith(serial_matcher)]

"""
"""

import logging

try:
    import pysetupdi

except ImportError:
    logging.warning("pysetupdi required for usb2can")
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
    for device in pysetupdi.devices(enumerator='USB'):
        instance_id = device.instance_id.strip('"')[-8:]
        if instance_id.startswith(serial_matcher):
            res.add(instance_id)

    return [ins_id for ins_id in res]


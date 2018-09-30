# coding: utf-8

"""
Defines common socketcan functions.
"""

import logging
import os
import errno
import struct
import sys
import subprocess
import re

from can.interfaces.socketcan.constants import CAN_EFF_FLAG

log = logging.getLogger(__name__)

def pack_filters(can_filters=None):
    if can_filters is None:
        # Pass all messages
        can_filters = [{
            'can_id': 0,
            'can_mask': 0
        }]

    can_filter_fmt = "={}I".format(2 * len(can_filters))
    filter_data = []
    for can_filter in can_filters:
        can_id = can_filter['can_id']
        can_mask = can_filter['can_mask']
        if 'extended' in can_filter:
            # Match on either 11-bit OR 29-bit messages instead of both
            can_mask |= CAN_EFF_FLAG
            if can_filter['extended']:
                can_id |= CAN_EFF_FLAG
        filter_data.append(can_id)
        filter_data.append(can_mask)

    return struct.pack(can_filter_fmt, *filter_data)


_PATTERN_CAN_INTERFACE = re.compile(r"v?can\d+")

def find_available_interfaces():
    """Returns the names of all open can/vcan interfaces using
    the ``ip link list`` command. If the lookup fails, an error
    is logged to the console and an empty list is returned.

    :rtype: an iterable of :class:`str`
    """

    try:
        # it might be good to add "type vcan", but that might (?) exclude physical can devices
        command = ["ip", "-o", "link", "list", "up"]
        output = subprocess.check_output(command, universal_newlines=True)

    except Exception as e: # subprocess.CalledProcessError was too specific
        log.error("failed to fetch opened can devices: %s", e)
        return []

    else:
        #log.debug("find_available_interfaces(): output=\n%s", output)
        # output contains some lines like "1: vcan42: <NOARP,UP,LOWER_UP> ..."
        # extract the "vcan42" of each line
        interface_names = [line.split(": ", 3)[1] for line in output.splitlines()]
        log.debug("find_available_interfaces(): detected: %s", interface_names)
        return filter(_PATTERN_CAN_INTERFACE.match, interface_names)

def error_code_to_str(code):
    """
    Converts a given error code (errno) to a useful and human readable string.

    :param int code: a possibly invalid/unknown error code
    :rtype: str
    :returns: a string explaining and containing the given error code, or a string
              explaining that the errorcode is unknown if that is the case
    """

    try:
        name = errno.errorcode[code]
    except KeyError:
        name = "UNKNOWN"

    try:
        description = os.strerror(code)
    except ValueError:
        description = "no description available"

    return "{} (errno {}): {}".format(name, code, description)

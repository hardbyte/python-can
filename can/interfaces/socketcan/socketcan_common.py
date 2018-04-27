#!/usr/bin/env python
# coding: utf-8

"""
Defines common socketcan functions.
"""

import logging
import os
import errno
import struct
import sys
if sys.version_info.major < 3: # and os.name == 'posix'
    import subprocess32 as subprocess
else:
    import subprocess

from can.interfaces.socketcan.socketcan_constants import CAN_EFF_FLAG

log = logging.getLogger('can.socketcan_common')

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

def find_available_interfaces():
    """Returns the names of all open can/vcan interfaces using
    the ``ip link list`` command. If the lookup fails, an error
    is logged to the console and an empty list is returned.

    :rtype: an iterable of :class:`str`
    """

    try:
        # it might be good to add "type vcan", but that might (?) exclude physical can devices
        command = ["ip", "-br", "-0", "link", "list", "up"]
        output = subprocess.check_output(command, universal_newlines=True)

    except subprocess.CalledProcessError as e:
        log.error("failed to fetch opened can devices: %s", e)
        return []

    else:
        # output contains some lines like "vcan42           UNKNOWN        <NOARP,UP,LOWER_UP>"
        # return the first entry of each line
        return [line.split()[0] for line in output.splitlines()]

def error_code_to_str(code):
    """
    Converts a given error code (errno) to a useful and human readable string.

    :param int error_code: a possibly invalid/unknown error code
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

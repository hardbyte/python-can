# coding: utf-8

"""
Defines common functions.
"""

import msgpack

from can import Message


def pack_message(message):
    as_dict = {
        "timestamp": message.timestamp,
        "arbitration_id": message.arbitration_id,
        "is_extended_id": message.is_extended_id,
        "is_remote_frame": message.is_remote_frame,
        "is_error_frame": message.is_error_frame,
        "channel": message.channel,
        "dlc": message.dlc,
        "data": message.data,
        "is_fd": message.is_fd,
        "bitrate_switch": message.bitrate_switch,
        "error_state_indicator": message.error_state_indicator,
    }
    return msgpack.packb(as_dict, use_bin_type=True)

def unpack_message(data):
    as_dict = msgpack.unpackb(data, raw=False)
    return Message(**as_dict)

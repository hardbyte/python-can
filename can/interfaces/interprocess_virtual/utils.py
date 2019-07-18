# coding: utf-8

"""
Defines common functions.
"""

import msgpack

from can import Message


def pack_message(message):
    """Pack a can.Message into a msgpack byte blob.
    """
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


def unpack_message(data, replace=dict(), check=False):
    """Unpack a can.Message from a msgpack byte blob.

    :raise TypeError: if the data contains key that are not valid arguments for can.Message
    :raise ValueError: if **check == True** and the message metadata is invalid in some way
    :raise Exception: if there was another problem while unpacking
    """
    as_dict = msgpack.unpackb(data, raw=False)
    as_dict.update(replace)
    return Message(check=check, **as_dict)

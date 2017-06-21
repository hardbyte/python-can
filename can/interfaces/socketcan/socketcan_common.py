# -*- coding: utf-8 -*-
"""
Defines common socketcan functions.
"""
import struct

from can.interfaces.socketcan.socketcan_constants import CAN_EFF_FLAG


def pack_filters(can_filters=None):
    if can_filters is None:
        # Pass all messages
        can_filters = [{
            'can_id': 0,
            'can_mask': 0,
            'extended': False
        }]

    can_filter_fmt = "={}I".format(2 * len(can_filters))
    filter_data = []
    for can_filter in can_filters:
        can_id = can_filter['can_id']
        if can_filter.get('extended'):
            can_id |= CAN_EFF_FLAG
        filter_data.append(can_id)
        filter_data.append(can_filter['can_mask'] | CAN_EFF_FLAG)
    return struct.pack(can_filter_fmt, *filter_data)

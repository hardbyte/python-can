#!/usr/bin/env python
# coding: utf-8

"""
Interfaces contain low level implementations that interact with CAN hardware.
"""

from pkg_resources import iter_entry_points

# TODO: isn't this a unnecessary information duplicate of `can/interface.py :: BACKENDS` (with the addition of 'socketcan')?
VALID_INTERFACES = set(['virtual',
                        'kvaser',
                        'serial',
                        'pcan',
                        'socketcan_ctypes', 'socketcan_native', 'socketcan',
                        'usb2can',
                        'ixxat',
                        'nican',
                        'iscan',
                        'vector',
                        'neovi',
                        'slcan',
                        'canal',
                       ])

VALID_INTERFACES.update(set([
    interface.name for interface in iter_entry_points('python_can.interface')
]))

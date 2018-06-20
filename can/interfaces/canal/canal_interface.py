#!/usr/bin/env python
# coding: utf-8

"""
"""

from __future__ import division, print_function, absolute_import

import logging

from can import BusABC, Message
from .canal_wrapper import *
from .serial_selector import find_serial

# Set up logging
log = logging.getLogger('can.canal')


def format_connection_string(deviceID, baudrate):
    """setup the string for the device

    config = deviceID + '; ' + baudrate
    """
    return "%s; %s" % (deviceID, baudrate)


def message_convert_tx(msg):
    messagetx = CanalMsg()

    length = msg.dlc
    messagetx.sizeData = length

    messagetx.id = msg.arbitration_id

    for i in range(length):
        messagetx.data[i] = msg.data[i]

    messagetx.flags = 0x80000000

    if msg.is_error_frame:
        messagetx.flags |= IS_ERROR_FRAME

    if msg.is_remote_frame:
        messagetx.flags |= IS_REMOTE_FRAME

    if msg.id_type:
        messagetx.flags |= IS_ID_TYPE

    return messagetx


def message_convert_rx(messagerx):
    """convert the message from the CANAL type to pythoncan type"""
    ID_TYPE = bool(messagerx.flags & IS_ID_TYPE)
    REMOTE_FRAME = bool(messagerx.flags & IS_REMOTE_FRAME)
    ERROR_FRAME = bool(messagerx.flags & IS_ERROR_FRAME)

    msgrx = Message(timestamp=messagerx.timestamp / 1000.0,
                    is_remote_frame=REMOTE_FRAME,
                    extended_id=ID_TYPE,
                    is_error_frame=ERROR_FRAME,
                    arbitration_id=messagerx.id,
                    dlc=messagerx.sizeData,
                    data=messagerx.data[:messagerx.sizeData])

    return msgrx


class CanalBus(BusABC):
    """Interface to a CANAL Bus. Works only on Windows.

    :param str channel:
        The device's serial number. If not provided, Windows Management Instrumentation
        will be used to identify the first such device.

    :param str dll (optional):
        Path to the DLL with the CANAL API to load
        Defaults to 'usb2can.dll'

    :param int bitrate (optional):
        Bitrate of channel in bit/s. Values will be limited to a maximum of 1000 Kb/s.
        Default is 500 Kbs

    :param str serialMatcher (optional):
        search string for automatic detection of the device serial

    :param int flags (optional):
        Flags to directly pass to open function of the CANAL abstraction layer.
    """

    def __init__(self, channel, dll='usb2can.dll', flags=0x00000008,
                 bitrate=500000, *args, **kwargs):

        self.can = CanalWrapper(kwargs[dll])

        if channel is None:
            # autodetect device
            # TODO: integrate into #51 some day
            if 'serialMatcher' in kwargs:
                channel = find_serial(kwargs["serialMatcher"])
            else:
                channel = find_serial()

            if not channel:
                raise can.CanError("Device ID could not be autodetected")

        self.channel_info = "CANAL device {}".format(channel)

        # convert to kb/s and cap: max rate is 1000 kb/s
        baudrate = min(int(bitrate // 1000), 1000)

        connector = format_connection_string(channel, baudrate)
        self.handle = self.can.open(connector, flags)

        super(CanalBus, self).__init__(channel=channel, dll=dll,
              flags=flags, bitrate=bitrate, *args, **kwargs)

    def send(self, msg, timeout=None):
        tx = message_convert_tx(msg)

        if timeout:
            status = self.can.blocking_send(self.handle, byref(tx), int(timeout * 1000))
        else:
            status = self.can.send(self.handle, byref(tx))

        if status != 0:
            raise can.CanError("could not send message: status == {}".format(status))

    def _recv_internal(self, timeout):

        messagerx = CanalMsg()

        if timeout == 0:
            status = self.can.receive(self.handle, byref(messagerx))

        else:
            time = 0 if timeout is None else int(timeout * 1000)
            status = self.can.blocking_receive(self.handle, byref(messagerx), time)

        if status == 0:
            # success
            return message_convert_rx(messagerx), False

        elif status == CANAL_ERROR_RCV_EMPTY or status == CANAL_ERROR_TIMEOUT:
            return None, False

        else:
            # unknown error
            raise can.CanError("could not receive message: status == {}".format(status))

    def shutdown(self):
        """
        Shuts down connection to the device safely.

        :raise cam.CanError: is closing the connection did not work
        """
        status = self.can.close(self.handle)

        if status != 0:
            raise can.CanError("could not shut down bus: status == {}".format(status))

#!/usr/bin/env python
# coding: utf-8

"""
"""

from __future__ import division
from __future__ import print_function

import logging

from can import BusABC, Message
from can.interfaces.canal.canal_wrapper import *

# Set up logging
log = logging.getLogger('can.canal')


def format_connection_string(deviceID, baudrate):
    """setup the string for the device

    config = deviceID + '; ' + baudrate
    """
    return "%s; %s" % (deviceID, baudrate)


def message_convert_tx(msg):
    messagetx = CanalMsg()

    length = len(msg.data)
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
                    data=messagerx.data[:messagerx.sizeData]
                    )

    return msgrx


class CanalBus(BusABC):
    """Interface to a CANAL Bus.

    Note the interface doesn't implement set_filters, or flush_tx_buffer methods.

    :param str channel:
        The device's serial number. If not provided, Windows Management Instrumentation
        will be used to identify the first such device. The *kwarg* `serial` may also be
        used.

    :param str dll:
        dll with CANAL API to load

    :param int bitrate:
        Bitrate of channel in bit/s. Values will be limited to a maximum of 1000 Kb/s.
        Default is 500 Kbs

    :param str serial (optional)
        device serial to use for the CANAL open call
    
    :param str serialMatcher (optional)
        search string for automatic detection of the device serial

    :param int flags:
        Flags to directly pass to open function of the CANAL abstraction layer.
    """

    def __init__(self, channel, *args, **kwargs):

        dll = kwargs.get('dll', can.rc.get('dll', None))
        if dll is None:
            raise Exception("please specify a CANAL dll to load, e.g. 'usb2can.dll'")

        self.can = CanalWrapper(dll)

        # set flags on the connection
        enable_flags = kwargs.get('flags', can.rc.get('flags', 0x00000008))

        # code to get the serial number of the device
        if 'serial' in kwargs:
            deviceID = kwargs["serial"]
        elif 'serial' in can.rc:
            deviceID = can.rc["serial"]
        elif channel is not None:
            deviceID = channel
        else:
            # autodetect device
            # TODO: integrate into #51 some day
            from can.interfaces.canal.serial_selector import serial
            if 'serialMatcher' in kwargs:
                deviceID = serial(kwargs["serialMatcher"])
            else:
                deviceID = serial()

            if not deviceID:
                raise can.CanError("Device ID could not be autodetected")

        self.channel_info = "CANAL device " + deviceID

        # get baudrate in bit/s
        baudrate = kwargs.get('bitrate', can.rc.get('bitrate', 500000))
        # convert to kb/s
        baudrate = baudrate // 1000
        # cap: max rate is 1000 kb/s
        baudrate = max(baudrate, 1000)

        connector = format_connection_string(deviceID, baudrate)

        self.handle = self.can.open(connector, enable_flags)

    def send(self, msg, timeout=None):
        tx = message_convert_tx(msg)

        if timeout:
            status = self.can.blocking_send(self.handle, byref(tx), int(timeout * 1000))
        else:
            status = self.can.send(self.handle, byref(tx))

        if status != 0:
            raise can.CanError("could not send message: status == {}".format(status))

    def recv(self, timeout=None):

        messagerx = CanalMsg()

        if timeout == 0:
            status = self.can.receive(self.handle, byref(messagerx))

        else:
            time = 0 if timeout is None else int(timeout * 1000)
            status = self.can.blocking_receive(self.handle, byref(messagerx), time)

        if status == 0:
            # success
            return message_convert_rx(messagerx)

        elif status == 19:
            # CANAL_ERROR_RCV_EMPTY
            log.warn("recv: status: CANAL_ERROR_RCV_EMPTY")
            return None

        elif status == 32:
            # CANAL_ERROR_TIMEOUT
            log.warn("recv: status: CANAL_ERROR_TIMEOUT")
            return None

        else:
            # another error
            raise can.CanError("could not receive message: status == {}".format(status))

    def shutdown(self):
        """Shut down the device safely"""
        status = self.can.close(self.handle)

        if status != 0:
            raise can.CanError("could not shut down bus: status == {}".format(status))

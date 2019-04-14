# coding: utf-8

"""
This interface is for Windows only, otherwise use socketCAN.
"""

from __future__ import division, print_function, absolute_import

import logging
from ctypes import byref

from can import BusABC, Message, CanError
from .usb2canabstractionlayer import *
from .serial_selector import find_serial_devices

# Set up logging
log = logging.getLogger('can.usb2can')


def message_convert_tx(msg):
    message_tx = CanalMsg()

    length = msg.dlc
    message_tx.sizeData = length

    message_tx.id = msg.arbitration_id

    for i in range(length):
        message_tx.data[i] = msg.data[i]

    message_tx.flags = 0x80000000

    if msg.is_error_frame:
        message_tx.flags |= IS_ERROR_FRAME

    if msg.is_remote_frame:
        message_tx.flags |= IS_REMOTE_FRAME

    if msg.is_extended_id:
        message_tx.flags |= IS_ID_TYPE

    return message_tx


def message_convert_rx(message_rx):
    """convert the message from the CANAL type to pythoncan type"""
    is_extended_id = bool(message_rx.flags & IS_ID_TYPE)
    is_remote_frame = bool(message_rx.flags & IS_REMOTE_FRAME)
    is_error_frame = bool(message_rx.flags & IS_ERROR_FRAME)

    return Message(timestamp=message_rx.timestamp,
                   is_remote_frame=is_remote_frame,
                   is_extended_id=is_extended_id,
                   is_error_frame=is_error_frame,
                   arbitration_id=message_rx.id,
                   dlc=message_rx.sizeData,
                   data=message_rx.data[:message_rx.sizeData])


class Usb2canBus(BusABC):
    """Interface to a USB2CAN Bus.

    This interface only works on Windows.
    Please use socketcan on Linux.

    :param str channel (optional):
        The device's serial number. If not provided, Windows Management Instrumentation
        will be used to identify the first such device.

    :param int bitrate (optional):
        Bitrate of channel in bit/s. Values will be limited to a maximum of 1000 Kb/s.
        Default is 500 Kbs

    :param int flags (optional):
        Flags to directly pass to open function of the usb2can abstraction layer.

    :param str dll (optional):
        Path to the DLL with the CANAL API to load
        Defaults to 'usb2can.dll'

    :param str serial (optional):
        Alias for `channel` that is provided for legacy reasons.
        If both `serial` and `channel` are set, `serial` will be used and
        channel will be ignored.

    """

    def __init__(self, channel=None, dll="usb2can.dll", flags=0x00000008,
                 bitrate=500000, *args, **kwargs):

        self.can = Usb2CanAbstractionLayer(dll)

        # get the serial number of the device
        if "serial" in kwargs:
            device_id = kwargs["serial"]
        else:
            device_id = channel

        # search for a serial number if the device_id is None or empty
        if not device_id:
            devices = find_serial_devices()
            if not devices:
                raise CanError("could not automatically find any device")
            device_id = devices[0]

        # convert to kb/s and cap: max rate is 1000 kb/s
        baudrate = min(int(bitrate // 1000), 1000)

        self.channel_info = "USB2CAN device {}".format(device_id)

        connector = "{}; {}".format(device_id, baudrate)
        self.handle = self.can.open(connector, flags)

        super(Usb2canBus, self).__init__(channel=channel, dll=dll, flags=flags,
                                         bitrate=bitrate, *args, **kwargs)

    def send(self, msg, timeout=None):
        tx = message_convert_tx(msg)

        if timeout:
            status = self.can.blocking_send(self.handle, byref(tx), int(timeout * 1000))
        else:
            status = self.can.send(self.handle, byref(tx))

        if status != CANAL_ERROR_SUCCESS:
            raise CanError("could not send message: status == {}".format(status))


    def _recv_internal(self, timeout):

        messagerx = CanalMsg()

        if timeout == 0:
            status = self.can.receive(self.handle, byref(messagerx))

        else:
            time = 0 if timeout is None else int(timeout * 1000)
            status = self.can.blocking_receive(self.handle, byref(messagerx), time)

        if status == CANAL_ERROR_SUCCESS:
            rx = message_convert_rx(messagerx)
        elif status == CANAL_ERROR_RCV_EMPTY or status == CANAL_ERROR_TIMEOUT:
            rx = None
        else:
            log.error('Canal Error %s', status)
            rx = None

        return rx, False

    def shutdown(self):
        """
        Shuts down connection to the device safely.

        :raise cam.CanError: is closing the connection did not work
        """
        status = self.can.close(self.handle)

        if status != CANAL_ERROR_SUCCESS:
            raise CanError("could not shut down bus: status == {}".format(status))

    @staticmethod
    def _detect_available_configs(serial_matcher=None):
        """
        Uses the Windows Management Instrumentation to identify serial devices.

        :param str serial_matcher (optional):
            search string for automatic detection of the device serial
        """
        if serial_matcher:
            channels = find_serial_devices(serial_matcher)
        else:
            channels = find_serial_devices()

        return [{'interface': 'usb2can', 'channel': c} for c in channels]

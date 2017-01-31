# this interface is for windows only, otherwise use socketCAN

import logging

from can import BusABC, Message
from can.interfaces.usb2can.usb2canabstractionlayer import *

bootTimeEpoch = 0
try:
    import uptime
    import datetime

    bootTimeEpoch = (uptime.boottime() - datetime.datetime.utcfromtimestamp(0)).total_seconds()
except:
    bootTimeEpoch = 0

# Set up logging
log = logging.getLogger('can.usb2can')


def format_connection_string(deviceID, baudrate='500'):
    """setup the string for the device

    config = deviceID + '; ' + baudrate
    """
    return "%s; %s" % (deviceID, baudrate)


# TODO: Issue 36 with data being zeros or anything other than 8 must be fixed
def message_convert_tx(msg):
    messagetx = CanalMsg()

    length = len(msg.data)
    messagetx.sizeData = length

    messagetx.id = msg.arbitration_id

    for i in range(length):
        messagetx.data[i] = msg.data[i]

    messagetx.flags = 80000000

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

    msgrx = Message(timestamp=messagerx.timestamp,
                    is_remote_frame=REMOTE_FRAME,
                    extended_id=ID_TYPE,
                    is_error_frame=ERROR_FRAME,
                    arbitration_id=messagerx.id,
                    dlc=messagerx.sizeData,
                    data=messagerx.data[:messagerx.sizeData]
                    )

    return msgrx


class Usb2canBus(BusABC):
    """Interface to a USB2CAN Bus.

    Note the USB2CAN interface doesn't implement set_filters, or flush_tx_buffer methods.

    :param str channel:
        The device's serial number. If not provided, Windows Management Instrumentation
        will be used to identify the first such device. The *kwarg* `serial` may also be
        used.

    :param int bitrate:
        Bitrate of channel in bit/s. Values will be limited to a maximum of 1000 Kb/s.
        Default is 500 Kbs

    :param int flags:
        Flags to directly pass to open function of the usb2can abstraction layer.
    """

    def __init__(self, channel, *args, **kwargs):

        self.can = Usb2CanAbstractionLayer()

        # set flags on the connection
        if 'flags' in kwargs:
            enable_flags = kwargs["flags"]

        else:
            enable_flags = 0x00000008

        # code to get the serial number of the device
        if 'serial' in kwargs:
            deviceID = kwargs["serial"]
        elif channel is not None:
            deviceID = channel
        else:
            from can.interfaces.usb2can.serial_selector import serial
            deviceID = serial()

        # set baudrate in kb/s from bitrate
        # (eg:500000 bitrate must be 500)
        if 'bitrate' in kwargs:
            br = kwargs["bitrate"]

            # max rate is 1000 kbps
            baudrate = max(1000, int(br/1000))
        # set default value
        else:
            baudrate = 500

        connector = format_connection_string(deviceID, baudrate)

        self.handle = self.can.open(connector, enable_flags)

    def send(self, msg, timeout=None):
        tx = message_convert_tx(msg)
        if timeout:
            self.can.blocking_send(self.handle, byref(tx), int(timeout * 1000))
        else:
            self.can.send(self.handle, byref(tx))

    def recv(self, timeout=None):

        messagerx = CanalMsg()

        if timeout == 0:
            status = self.can.receive(self.handle, byref(messagerx))

        else:
            time = 0 if timeout is None else int(timeout * 1000)
            status = self.can.blocking_receive(self.handle, byref(messagerx), time)

        if status == 0:
            rx = message_convert_rx(messagerx)
        elif status == 19 or status == 32:
            # CANAL_ERROR_RCV_EMPTY or CANAL_ERROR_TIMEOUT
            rx = None
        else:
            log.error('Canal Error %s', status)
            rx = None

        return rx

    def shutdown(self):
        """Shut down the device safely"""
        status = self.can.close(self.handle)

# this interface is for windows only, otherwise use socketCAN

import logging

logger = logging.getLogger('can.usb2can')


from can.bus import BusABC
from can.message import Message
from can.interfaces.usb2can import *
from can.interfaces.usb2canSerialFindWin import serial

bootTimeEpoch = 0
try:
    import uptime
    import datetime

    bootTimeEpoch = (uptime.boottime() - datetime.datetime.utcfromtimestamp(0)).total_seconds()
except:
    bootTimeEpoch = 0

# Set up logging
logging.basicConfig(level=logging.WARNING)
log = logging.getLogger('can.usb2can')


# setup the string for the device
def set_string(deviceID, baudrate='500'):
    # config = deviceID + '; ' + baudrate
    config = "%s; %s" % (deviceID, baudrate)

    return (config)


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


# interface functions
class Usb2canBus(BusABC):
    def __init__(self, channel, *args, **kwargs):

        self.can = usb2can()

        enable_flags = c_ulong

        # set flags on the connection
        if 'flags' in kwargs:
            enable_flags = kwargs["flags"]

        else:
            enable_flags = 0x00000008

        # code to get the serial number of the device
        if 'serial' in kwargs:

            deviceID = kwargs["serial"]

        else:
            deviceID = serial()

        # set baudrate
        if 'baud' in kwargs:

            br = kwargs["baud"]

            # set custom baud rate (ex:500000 bitrate must be 500)
            # max rate is 1000 kbps
            baudrate = int(br)

        # set default value
        else:
            baudrate = 500

        connector = set_string(deviceID, baudrate)

        self.handle = self.can.CanalOpen(connector, enable_flags)

    def send(self, msg):

        tx = message_convert_tx(msg)
        self.can.CanalSend(self.handle, byref(tx))

    def recv(self, timeout=None):

        messagerx = CanalMsg()

        if timeout is None:
            status = self.can.CanalReceive(self.handle, byref(messagerx))

        else:
            time = c_ulong
            time = timeout
            status = self.can.CanalBlockingReceive(self.handle, byref(messagerx), time)

        if status is 0:
            rx = message_convert_rx(messagerx)
        else:
            logger.error('Canal Error %s', status)
            rx = None

        return rx

    def shutdown(self):
        """Shut down the device safely"""
        status = self.can.CanalClose(self.handle)

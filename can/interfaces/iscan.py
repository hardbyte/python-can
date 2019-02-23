# coding: utf-8

"""
Interface for isCAN from Thorsis Technologies GmbH, former ifak system GmbH.
"""

from __future__ import absolute_import, division

import ctypes
import time
import logging

from can import CanError, BusABC, Message

logger = logging.getLogger(__name__)

CanData = ctypes.c_ubyte * 8


class MessageExStruct(ctypes.Structure):
    _fields_ = [
        ("message_id", ctypes.c_ulong),
        ("is_extended", ctypes.c_ubyte),
        ("remote_req", ctypes.c_ubyte),
        ("data_len", ctypes.c_ubyte),
        ("data", CanData),
    ]


def check_status(result, function, arguments):
    if result > 0:
        raise IscanError(function, result, arguments)
    return result


try:
    iscan = ctypes.cdll.LoadLibrary("iscandrv")
except OSError as e:
    iscan = None
    logger.warning("Failed to load IS-CAN driver: %s", e)
else:
    iscan.isCAN_DeviceInitEx.argtypes = [ctypes.c_ubyte, ctypes.c_ubyte]
    iscan.isCAN_DeviceInitEx.errcheck = check_status
    iscan.isCAN_DeviceInitEx.restype = ctypes.c_ubyte
    iscan.isCAN_ReceiveMessageEx.errcheck = check_status
    iscan.isCAN_ReceiveMessageEx.restype = ctypes.c_ubyte
    iscan.isCAN_TransmitMessageEx.errcheck = check_status
    iscan.isCAN_TransmitMessageEx.restype = ctypes.c_ubyte
    iscan.isCAN_CloseDevice.errcheck = check_status
    iscan.isCAN_CloseDevice.restype = ctypes.c_ubyte


class IscanBus(BusABC):
    """isCAN interface"""

    BAUDRATES = {
        5000: 0,
        10000: 1,
        20000: 2,
        50000: 3,
        100000: 4,
        125000: 5,
        250000: 6,
        500000: 7,
        800000: 8,
        1000000: 9
    }

    def __init__(self, channel, bitrate=500000, poll_interval=0.01, **kwargs):
        """
        :param int channel:
            Device number
        :param int bitrate:
            Bitrate in bits/s
        :param float poll_interval:
            Poll interval in seconds when reading messages
        """
        if iscan is None:
            raise ImportError("Could not load isCAN driver")

        self.channel = ctypes.c_ubyte(int(channel))
        self.channel_info = "IS-CAN: %s" % channel

        if bitrate not in self.BAUDRATES:
            valid_bitrates = ", ".join(str(bitrate) for bitrate in self.BAUDRATES)
            raise ValueError("Invalid bitrate, choose one of " + valid_bitrates)

        self.poll_interval = poll_interval
        iscan.isCAN_DeviceInitEx(self.channel, self.BAUDRATES[bitrate])

        super(IscanBus, self).__init__(channel=channel, bitrate=bitrate,
            poll_interval=poll_interval, **kwargs)

    def _recv_internal(self, timeout):
        raw_msg = MessageExStruct()
        end_time = time.time() + timeout if timeout is not None else None
        while True:
            try:
                iscan.isCAN_ReceiveMessageEx(self.channel, ctypes.byref(raw_msg))
            except IscanError as e:
                if e.error_code != 8:
                    # An error occurred
                    raise
                if end_time is not None and time.time() > end_time:
                    # No message within timeout
                    return None, False
                # Sleep a short time to avoid hammering
                time.sleep(self.poll_interval)
            else:
                # A message was received
                break

        msg = Message(arbitration_id=raw_msg.message_id,
                      is_extended_id=bool(raw_msg.is_extended),
                      timestamp=time.time(),                    # Better than nothing...
                      is_remote_frame=bool(raw_msg.remote_req),
                      dlc=raw_msg.data_len,
                      data=raw_msg.data[:raw_msg.data_len],
                      channel=self.channel.value)
        return msg, False

    def send(self, msg, timeout=None):
        raw_msg = MessageExStruct(msg.arbitration_id,
                                  bool(msg.is_extended_id),
                                  bool(msg.is_remote_frame),
                                  msg.dlc,
                                  CanData(*msg.data))
        iscan.isCAN_TransmitMessageEx(self.channel, ctypes.byref(raw_msg))

    def shutdown(self):
        iscan.isCAN_CloseDevice(self.channel)


class IscanError(CanError):
    # TODO: document

    ERROR_CODES = {
        1: "No access to device",
        2: "Device with ID not found",
        3: "Driver operation failed",
        4: "Invalid parameter",
        5: "Operation allowed only in online state",
        6: "Device timeout",
        7: "Device is transmitting a message",
        8: "No message received",
        9: "Thread not started",
        10: "Thread already started",
        11: "Buffer overrun",
        12: "Device not initialized",
        15: "Found the device, but it is being used by another process",
        16: "Bus error",
        17: "Bus off",
        18: "Error passive",
        19: "Data overrun",
        20: "Error warning",
        30: "Send error",
        31: "Transmission not acknowledged on bus",
        32: "Error critical bus",
        35: "Callbackthread is blocked, stopping thread failed",
        40: "Need a licence number under NT4"
    }

    def __init__(self, function, error_code, arguments):
        super(IscanError, self).__init__()
        # :Status code
        self.error_code = error_code
        # :Function that failed
        self.function = function
        # :Arguments passed to function
        self.arguments = arguments

    def __str__(self):
        description = self.ERROR_CODES.get(self.error_code,
                                           "Error code %d" % self.error_code)
        return "Function %s failed: %s" % (self.function.__name__, description)

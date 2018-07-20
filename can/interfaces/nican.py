#!/usr/bin/env python
# coding: utf-8

"""
NI-CAN interface module.

Implementation references:
* http://www.ni.com/pdf/manuals/370289c.pdf
* https://github.com/buendiya/NicanPython

TODO: We could implement this interface such that setting other filters
      could work when the initial filters were set to zero using the
      software fallback. Or could the software filters even be changed
      after the connection was opened? We need to document that bahaviour!
      See also the IXXAT interface.

"""

import ctypes
import logging
import sys

from can import CanError, BusABC, Message

logger = logging.getLogger(__name__)

NC_SUCCESS =            0
NC_ERR_TIMEOUT =        1
TIMEOUT_ERROR_CODE =    -1074388991

NC_DURATION_INFINITE =  0xFFFFFFFF

NC_OP_START =           0x80000001
NC_OP_STOP  =           0x80000002
NC_OP_RESET =           0x80000003

NC_FRMTYPE_REMOTE =     1
NC_FRMTYPE_COMM_ERR =   2

NC_ST_READ_AVAIL =      0x00000001
NC_ST_WRITE_SUCCESS =   0x00000002
NC_ST_ERROR =           0x00000010
NC_ST_WARNING =         0x00000020

NC_ATTR_BAUD_RATE =     0x80000007
NC_ATTR_START_ON_OPEN = 0x80000006
NC_ATTR_READ_Q_LEN =    0x80000013
NC_ATTR_WRITE_Q_LEN =   0x80000014
NC_ATTR_CAN_COMP_STD =  0x80010001
NC_ATTR_CAN_MASK_STD =  0x80010002
NC_ATTR_CAN_COMP_XTD =  0x80010003
NC_ATTR_CAN_MASK_XTD =  0x80010004
NC_ATTR_LOG_COMM_ERRS = 0x8001000A

NC_FL_CAN_ARBID_XTD =   0x20000000

CanData = ctypes.c_ubyte * 8


class RxMessageStruct(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("timestamp", ctypes.c_ulonglong),
        ("arb_id", ctypes.c_ulong),
        ("frame_type", ctypes.c_ubyte),
        ("dlc", ctypes.c_ubyte),
        ("data", CanData),
    ]

class TxMessageStruct(ctypes.Structure):
    _fields_ = [
        ("arb_id", ctypes.c_ulong),
        ("is_remote", ctypes.c_ubyte),
        ("dlc", ctypes.c_ubyte),
        ("data", CanData),
    ]


def check_status(result, function, arguments):
    if result > 0:
        logger.warning(get_error_message(result))
    elif result < 0:
        raise NicanError(function, result, arguments)
    return result


def get_error_message(status_code):
    """Convert status code to descriptive string."""
    errmsg = ctypes.create_string_buffer(1024)
    nican.ncStatusToString(status_code, len(errmsg), errmsg)
    return errmsg.value.decode("ascii")


if sys.platform == "win32":
    try:
        nican = ctypes.windll.LoadLibrary("nican")
    except Exception as e:
        nican = None
        logger.error("Failed to load NI-CAN driver: %s", e)
    else:
        nican.ncConfig.argtypes = [
            ctypes.c_char_p, ctypes.c_ulong, ctypes.c_void_p, ctypes.c_void_p]
        nican.ncConfig.errcheck = check_status
        nican.ncOpenObject.argtypes = [ctypes.c_char_p, ctypes.c_void_p]
        nican.ncOpenObject.errcheck = check_status
        nican.ncCloseObject.errcheck = check_status
        nican.ncAction.argtypes = [ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong]
        nican.ncAction.errcheck = check_status
        nican.ncRead.errcheck = check_status
        nican.ncWrite.errcheck = check_status
        nican.ncWaitForState.argtypes = [
            ctypes.c_ulong, ctypes.c_ulong, ctypes.c_ulong, ctypes.c_void_p]
        nican.ncWaitForState.errcheck = check_status
        nican.ncStatusToString.argtypes = [
            ctypes.c_int, ctypes.c_uint, ctypes.c_char_p]
else:
    nican = None
    logger.warning("NI-CAN interface is only available on Windows systems")

class NicanBus(BusABC):
    """
    The CAN Bus implemented for the NI-CAN interface.

    .. warning::

        This interface does implement efficient filtering of messages, but
        the filters have to be set in :meth:`~can.interfaces.nican.NicanBus.__init__`
        using the ``can_filters`` parameter. Using :meth:`~can.interfaces.nican.NicanBus.set_filters`
        does not work.

    """

    def __init__(self, channel, can_filters=None, bitrate=None, log_errors=True, **kwargs):
        """
        :param str channel:
            Name of the object to open (e.g. 'CAN0')

        :param int bitrate:
            Bitrate in bits/s

        :param list can_filters:
            See :meth:`can.BusABC.set_filters`.

        :param bool log_errors:
            If True, communication errors will appear as CAN messages with
            ``is_error_frame`` set to True and ``arbitration_id`` will identify
            the error (default True)

        :raises can.interfaces.nican.NicanError:
            If starting communication fails

        """
        if nican is None:
            raise ImportError("The NI-CAN driver could not be loaded. "
                              "Check that you are using 32-bit Python on Windows.")

        self.channel = channel
        self.channel_info = "NI-CAN: " + channel
        if not isinstance(channel, bytes):
            channel = channel.encode()

        config = [
            (NC_ATTR_START_ON_OPEN, True),
            (NC_ATTR_LOG_COMM_ERRS, log_errors)
        ]

        if not can_filters:
            logger.info("Filtering has been disabled")
            config.extend([
                (NC_ATTR_CAN_COMP_STD, 0),
                (NC_ATTR_CAN_MASK_STD, 0),
                (NC_ATTR_CAN_COMP_XTD, 0),
                (NC_ATTR_CAN_MASK_XTD, 0)
            ])
        else:
            for can_filter in can_filters:
                can_id = can_filter["can_id"]
                can_mask = can_filter["can_mask"]
                logger.info("Filtering on ID 0x%X, mask 0x%X", can_id, can_mask)
                if can_filter.get("extended"):
                    config.extend([
                        (NC_ATTR_CAN_COMP_XTD, can_id | NC_FL_CAN_ARBID_XTD),
                        (NC_ATTR_CAN_MASK_XTD, can_mask)
                    ])
                else:
                    config.extend([
                        (NC_ATTR_CAN_COMP_STD, can_id),
                        (NC_ATTR_CAN_MASK_STD, can_mask),
                    ])

        if bitrate:
            config.append((NC_ATTR_BAUD_RATE, bitrate))

        AttrList = ctypes.c_ulong * len(config)
        attr_id_list = AttrList(*(row[0] for row in config))
        attr_value_list = AttrList(*(row[1] for row in config))
        nican.ncConfig(channel,
                       len(config),
                       ctypes.byref(attr_id_list),
                       ctypes.byref(attr_value_list))

        self.handle = ctypes.c_ulong()
        nican.ncOpenObject(channel, ctypes.byref(self.handle))

        super(NicanBus, self).__init__(channel=channel,
            can_filters=can_filters, bitrate=bitrate,
            log_errors=log_errors, **kwargs)

    def _recv_internal(self, timeout):
        """
        Read a message from a NI-CAN bus.

        :param float timeout:
            Max time to wait in seconds or None if infinite

        :raises can.interfaces.nican.NicanError:
            If reception fails
        """
        if timeout is None:
            timeout = NC_DURATION_INFINITE
        else:
            timeout = int(timeout * 1000)

        state = ctypes.c_ulong()
        try:
            nican.ncWaitForState(
                self.handle, NC_ST_READ_AVAIL, timeout, ctypes.byref(state))
        except NicanError as e:
            if e.error_code == TIMEOUT_ERROR_CODE:
                return None, True
            else:
                raise

        raw_msg = RxMessageStruct()
        nican.ncRead(self.handle, ctypes.sizeof(raw_msg), ctypes.byref(raw_msg))
        # http://stackoverflow.com/questions/6161776/convert-windows-filetime-to-second-in-unix-linux
        timestamp = raw_msg.timestamp / 10000000.0 - 11644473600
        is_remote_frame = raw_msg.frame_type == NC_FRMTYPE_REMOTE
        is_error_frame = raw_msg.frame_type == NC_FRMTYPE_COMM_ERR
        is_extended = bool(raw_msg.arb_id & NC_FL_CAN_ARBID_XTD)
        arb_id = raw_msg.arb_id
        if not is_error_frame:
            arb_id &= 0x1FFFFFFF
        dlc = raw_msg.dlc
        msg = Message(timestamp=timestamp,
                      channel=self.channel,
                      is_remote_frame=is_remote_frame,
                      is_error_frame=is_error_frame,
                      extended_id=is_extended,
                      arbitration_id=arb_id,
                      dlc=dlc,
                      data=raw_msg.data[:dlc])
        return msg, True

    def send(self, msg, timeout=None):
        """
        Send a message to NI-CAN.

        :param can.Message msg:
            Message to send

        :raises can.interfaces.nican.NicanError:
            If writing to transmit buffer fails.
            It does not wait for message to be ACKed currently.
        """
        arb_id = msg.arbitration_id
        if msg.id_type:
            arb_id |= NC_FL_CAN_ARBID_XTD
        raw_msg = TxMessageStruct(arb_id,
                                  bool(msg.is_remote_frame),
                                  msg.dlc,
                                  CanData(*msg.data))
        nican.ncWrite(
            self.handle, ctypes.sizeof(raw_msg), ctypes.byref(raw_msg))

        # TODO:
        # ncWaitForState can not be called here if the recv() method is called
        # from a different thread, which is a very common use case.
        # Maybe it is possible to use ncCreateNotification instead but seems a
        # bit overkill at the moment.
        #state = ctypes.c_ulong()
        #nican.ncWaitForState(
        #    self.handle, NC_ST_WRITE_SUCCESS, int(timeout * 1000), ctypes.byref(state))

    def reset(self):
        """
        Resets network interface. Stops network interface, then resets the CAN
        chip to clear the CAN error counters (clear error passive state).
        Resetting includes clearing all entries from read and write queues.
        """
        nican.ncAction(self.handle, NC_OP_RESET, 0)

    def shutdown(self):
        """Close object."""
        nican.ncCloseObject(self.handle)

    __set_filters_has_been_called = False
    def set_filters(self, can_filers=None):
        """Unsupported. See note on :class:`~can.interfaces.nican.NicanBus`.
        """
        if self.__set_filters_has_been_called:
            logger.warn("using filters is not supported like this, see note on NicanBus")
        else:
            # allow the constructor to call this without causing a warning
            self.__set_filters_has_been_called = True


class NicanError(CanError):
    """Error from NI-CAN driver."""

    def __init__(self, function, error_code, arguments):
        super(NicanError, self).__init__()
        #: Status code
        self.error_code = error_code
        #: Function that failed
        self.function = function
        #: Arguments passed to function
        self.arguments = arguments

    def __str__(self):
        return "Function %s failed:\n%s" % (
            self.function.__name__, get_error_message(self.error_code))

# -*- coding: utf-8 -*-
"""
Contains Python equivalents of the function and constant
definitions in CANLIB's canlib.h, with some supporting functionality
specific to Python.

Copyright (C) 2010 Dynamic Controls
"""

import sys
import time
import logging
import threading
try:
    import queue as queue
except ImportError:
    import Queue as queue
import ctypes

log = logging.getLogger('can.canlib')
log.setLevel(logging.ERROR)

from can import CanError, BusABC
from can import Message as MessageBase
from can.interfaces.kvaser import constants as canstat

try:
    if sys.platform == "win32":
        __canlib = ctypes.windll.LoadLibrary("canlib32")
    else:
        __canlib = ctypes.cdll.LoadLibrary("libcanlib.so")
    log.info("loaded kvaser's CAN library")
except OSError:
    log.warning("Kvaser canlib is unavailable.")
    __canlib = None


def __get_canlib_function(func_name, argtypes=None, restype=None, errcheck=None):
    log.debug('Wrapping function "%s"' % func_name)
    try:
        # e.g. canlib.canBusOn
        retval = getattr(__canlib, func_name)
        log.debug('Function found in library')
    except AttributeError:
        log.warning('Function was not found in library')
    else:
        log.debug('Result type is: %s' % type(restype))
        #log.debug('Error check function is: %s' % errcheck)
        retval.argtypes = argtypes
        retval.restype = restype
        retval.errcheck = errcheck
        return retval


class CANLIBError(CanError):

    """
    Try to display errors that occur within the wrapped C library nicely.
    """

    def __init__(self, function, error_code, arguments):
        super(CANLIBError, self).__init__()
        self.error_code = error_code
        self.function = function
        self.arguments = arguments

    def __str__(self):
        return "function %s failed - %s - arguments were %s" % (self.function.__name__,
                                                                self.__get_error_message(),
                                                                self.arguments)

    def __get_error_message(self):
        errmsg = ctypes.create_string_buffer(128)
        canGetErrorText(self.error_code, errmsg, len(errmsg))
        return "%s (code %d)" % (errmsg.value, self.error_code)


class ChannelNotFoundError(CANLIBError):
    pass


class Message(MessageBase):
    """
    The canlib sdk requires the flags to be calculated so we extend Message.
    """

    def __init__(self, *args, **kwargs):
        super(Message, self).__init__(*args, **kwargs)
        self.flags = 0
        self.flags |= (self.id_type * canstat.canMSG_EXT)
        self.flags &= (0xFFFF - canstat.canMSG_RTR)
        self.flags |= (self.is_remote_frame * canstat.canMSG_RTR)
        self.flags &= (0xFFFF - canstat.canMSG_WAKEUP)
        self.flags &= (0xFFFF - canstat.canMSG_ERROR_FRAME)
        if self.is_error_frame:
            self.flags |= canstat.canMSG_ERROR_FRAME


def __convert_can_status_to_int(result):
    log.debug("converting can status to int {} ({})".format(result, type(result)))
    if isinstance(result, int):
        return result
    else:
        return result.value


def __check_status(result, function, arguments):
    result = __convert_can_status_to_int(result)
    if not canstat.CANSTATUS_SUCCESS(result):
        log.debug('Detected error while checking CAN status')
        raise CANLIBError(function, result, arguments)
    return result


def __check_status_read(result, function, arguments):
    result = __convert_can_status_to_int(result)
    if not canstat.CANSTATUS_SUCCESS(result) and result != canstat.canERR_NOMSG:
        log.debug('Detected error in which checking status read')
        raise CANLIBError(function, result, arguments)
    return result


class c_canHandle(ctypes.c_int):
    pass

canINVALID_HANDLE = -1


def __handle_is_valid(handle):
    return (handle.value > canINVALID_HANDLE)


def __check_bus_handle_validity(handle, function, arguments):
    if not __handle_is_valid(handle):
        raise CANLIBError(function, handle, arguments)
    else:
        return handle


canInitializeLibrary = __get_canlib_function("canInitializeLibrary",
                                             argtypes=[],
                                             restype=canstat.c_canStatus,
                                             errcheck=__check_status)

canGetErrorText = __get_canlib_function("canGetErrorText",
                                        argtypes=[canstat.c_canStatus, ctypes.c_char_p, ctypes.c_uint],
                                        restype=canstat.c_canStatus,
                                        errcheck=__check_status)

# TODO wrap this type of function to provide a more Pythonic API
canGetNumberOfChannels = __get_canlib_function("canGetNumberOfChannels",
                                               argtypes=[ctypes.c_void_p],
                                               restype=canstat.c_canStatus,
                                               errcheck=__check_status)

if sys.platform == "win32":
    __canReadTimer_func_name = "kvReadTimer"
else:
    __canReadTimer_func_name = "canReadTimer"
canReadTimer = __get_canlib_function(__canReadTimer_func_name,
                                     argtypes=[c_canHandle, ctypes.c_void_p],
                                     restype=canstat.c_canStatus,
                                     errcheck=__check_status)

canBusOff = __get_canlib_function("canBusOff",
                                  argtypes=[c_canHandle],
                                  restype=canstat.c_canStatus,
                                  errcheck=__check_status)

canBusOn = __get_canlib_function("canBusOn",
                                 argtypes=[c_canHandle],
                                 restype=canstat.c_canStatus,
                                 errcheck=__check_status)

canClose = __get_canlib_function("canClose",
                                 argtypes=[c_canHandle],
                                 restype=canstat.c_canStatus,
                                 errcheck=__check_status)

canOPEN_EXCLUSIVE = 0x0008
canOPEN_REQUIRE_EXTENDED = 0x0010
canOPEN_ACCEPT_VIRTUAL = 0x0020
canOPEN_OVERRIDE_EXCLUSIVE = 0x0040
canOPEN_REQUIRE_INIT_ACCESS = 0x0080
canOPEN_NO_INIT_ACCESS = 0x0100
canOPEN_ACCEPT_LARGE_DLC = 0x0200

FLAGS_MASK = (canOPEN_EXCLUSIVE | canOPEN_REQUIRE_EXTENDED |
              canOPEN_ACCEPT_VIRTUAL | canOPEN_OVERRIDE_EXCLUSIVE |
              canOPEN_REQUIRE_INIT_ACCESS | canOPEN_NO_INIT_ACCESS |
              canOPEN_ACCEPT_LARGE_DLC)

canOpenChannel = __get_canlib_function("canOpenChannel",
                                       argtypes=[ctypes.c_int, ctypes.c_int],
                                       restype=c_canHandle,
                                       errcheck=__check_bus_handle_validity)

canSetBusParams = __get_canlib_function("canSetBusParams",
                                        argtypes=[c_canHandle, ctypes.c_long,
                                                  ctypes.c_uint, ctypes.c_uint,
                                                  ctypes.c_uint, ctypes.c_uint,
                                                  ctypes.c_uint],
                                        restype=canstat.c_canStatus,
                                        errcheck=__check_status)


canSetBusOutputControl = __get_canlib_function("canSetBusOutputControl",
                                               argtypes=[c_canHandle,
                                                         ctypes.c_uint],
                                               restype=canstat.c_canStatus,
                                               errcheck=__check_status)

canSetAcceptanceFilter = __get_canlib_function("canSetAcceptanceFilter",
                                               argtypes=[
                                                   c_canHandle,
                                                   ctypes.c_uint,
                                                   ctypes.c_uint,
                                                   ctypes.c_int
                                               ],
                                               restype=canstat.c_canStatus,
                                               errcheck=__check_status)

canReadWait = __get_canlib_function("canReadWait",
                                    argtypes=[c_canHandle, ctypes.c_void_p,
                                              ctypes.c_void_p, ctypes.c_void_p,
                                              ctypes.c_void_p, ctypes.c_void_p,
                                              ctypes.c_long],
                                    restype=canstat.c_canStatus,
                                    errcheck=__check_status_read)

canWriteWait = __get_canlib_function("canWriteWait",
                                     argtypes=[
                                         c_canHandle,
                                         ctypes.c_long,
                                         ctypes.c_void_p,
                                         ctypes.c_uint,
                                         ctypes.c_uint,
                                         ctypes.c_ulong],
                                     restype=canstat.c_canStatus,
                                     errcheck=__check_status)


canIoCtl = __get_canlib_function("canIoCtl",
                                 argtypes=[c_canHandle, ctypes.c_uint,
                                           ctypes.c_void_p, ctypes.c_uint],
                                 restype=canstat.c_canStatus,
                                 errcheck=__check_status)

canGetVersion = __get_canlib_function("canGetVersion",
                                      restype=ctypes.c_short,
                                      errcheck=__check_status)

if sys.platform == "win32":
    canGetVersionEx = __get_canlib_function("canGetVersionEx",
                                            argtypes=[ctypes.c_uint],
                                            restype=ctypes.c_uint,
                                            errcheck=__check_status)


def init_kvaser_library():
    try:
        log.debug("Initializing Kvaser CAN library")
        canInitializeLibrary()
        log.debug("CAN library initialized")
    except:
        log.warning("Kvaser canlib is unavailable.")


def lookup_transceiver_type(typename):
    if typename in canstat.canTransceiverTypeStrings:
        return canstat.canTransceiverTypeStrings[typename]
    else:
        log.warning("Unknown transceiver type - add to list?")
        return "unknown"


canGetChannelData = __get_canlib_function("canGetChannelData",
                                          argtypes=[ctypes.c_int,
                                                    ctypes.c_int,
                                                    ctypes.c_void_p,
                                                    ctypes.c_size_t],
                                          restype=canstat.c_canStatus,
                                          errcheck=__check_status)


DRIVER_MODE_SILENT = False
DRIVER_MODE_NORMAL = True


class KvaserBus(BusABC):
    """
    The CAN Bus implemented for the Kvaser interface.
    """

    def __init__(self, channel, can_filters=None, **config):
        """
        :param int channel:
            The Channel id to create this bus with.

        Backend Configuration
        ---------------------

        :param int bitrate:
            Bitrate of channel in bit/s
        :param int tseg1:
        :param int tseg2:
        :param int sjw:
            Synchronisation Jump Width decides the maximum number of time quanta
            that the controller can resynchronise every bit.
        :param no_samp:
            Some CAN controllers can also sample each bit three times.
            In this case, the bit will be sampled three quanta in a row,
            with the last sample being taken in the edge between TSEG1 and TSEG2.
            Three samples should only be used for relatively slow baudrates.

        :param bool driver_mode:
            Silent or normal.
        """
        log.info("CAN Filters: {}".format(can_filters))
        log.info("Got configuration of: {}".format(config))
        bitrate = config.get('bitrate', 500000)
        tseg1 = config.get('tseg1', 4)
        tseg2 = config.get('tseg2', 3)
        sjw = config.get('sjw', 1)
        no_samp = config.get('no_samp', 1)
        driver_mode = config.get('driver_mode', DRIVER_MODE_NORMAL)
        single_handle = config.get('single_handle', False)

        log.debug('Initialising bus instance')
        self.single_handle = single_handle

        num_channels = ctypes.c_int(0)
        res = canGetNumberOfChannels(ctypes.byref(num_channels))
        log.debug("Res: {}".format(res))
        num_channels = int(num_channels.value)
        log.info('Found %d available channels' % num_channels)

        if self.single_handle:
            self.writing_event = threading.Event()
            self.done_writing = threading.Condition()

        log.debug('Creating read handle to bus channel: %s' % channel)
        self._read_handle = canOpenChannel(channel, canOPEN_ACCEPT_VIRTUAL)
        canIoCtl(self._read_handle, canstat.canIOCTL_SET_TIMER_SCALE, ctypes.byref(ctypes.c_long(1)), 4)
        canSetBusParams(self._read_handle, bitrate, tseg1, tseg2, sjw, no_samp, 0)

        if can_filters is not None and len(can_filters):
            log.warning("The kvaser canlib backend is filtering messages")
            code, mask = 0, 0
            for can_filter in can_filters:
                code |= can_filter['can_id']
                mask |= can_filter['can_mask']
            log.warning("Filtering on: {}  {}".format(code, mask))
            canSetAcceptanceFilter(self._read_handle, code, mask, 1)

        if self.single_handle:
            log.debug("We don't require separate handles to the bus")
            self._write_handle = self._read_handle
        else:
            log.debug('Creating separate handle for TX on channel: %s' % channel)
            self._write_handle = canOpenChannel(channel, canOPEN_ACCEPT_VIRTUAL)
            canBusOn(self._read_handle)

        can_driver_mode = canstat.canDRIVER_SILENT if driver_mode == DRIVER_MODE_SILENT else canstat.canDRIVER_NORMAL
        canSetBusOutputControl(self._write_handle, can_driver_mode)
        log.debug('Going bus on TX handle')
        canBusOn(self._write_handle)

        if driver_mode == DRIVER_MODE_SILENT:
            self.__write_process = lambda: None

        self.timer_offset = None  # Used to zero the timestamps from the first message

        '''
        Approximate offset between time.time() and CAN timestamps (~2ms accuracy)
        There will always be some lag between when the message is on the bus to
        when it reaches Python. Allow messages to be on the bus for a while before
        reading this value so it has a chance to correct itself
        '''
        self.pc_time_offset = None

        super(KvaserBus, self).__init__()

    def flush_tx_buffer(self):
        """
        Flushes the transmit buffer on the Kvaser
        """
        canIoCtl(self._write_handle, canstat.canIOCTL_FLUSH_TX_BUFFER, 0, 0)

    def __convert_timestamp(self, value):
        # The kvaser seems to zero times
        # Use the current value if the offset has not been set yet
        if not hasattr(self, 'timer_offset') or self.timer_offset is None:
            self.timer_offset = value
            self.pc_time_offset = time.time()

        if value < self.timer_offset:  # Check for overflow
            MAX_32BIT = 0xFFFFFFFF  # The maximum value that the timer reaches on a 32-bit machine
            MAX_64BIT = 0x9FFFFFFFF  # The maximum value that the timer reaches on a 64-bit machine
            if ctypes.sizeof(ctypes.c_long) == 8:
                value += MAX_64BIT
            elif ctypes.sizeof(ctypes.c_long) == 4:
                value += MAX_32BIT
            else:
                raise CanError('Unknown platform. Expected a long to be 4 or 8 bytes long but it was %i bytes.' % ctypes.sizeof(ctypes.c_long))
            if value <= self.timer_offset:
                raise OverflowError('CAN timestamp overflowed. The timer offset was ' + str(self.timer_offset))

        timestamp = (float(value - self.timer_offset) / 1000000)  # Convert from us into seconds
        lag = (time.time() - self.pc_time_offset) - timestamp
        if lag < 0:
            # If we see a timestamp that is quicker than the ever before, update the offset
            self.pc_time_offset += lag
        return timestamp

    def recv(self, timeout=None):
        """
        Read a message from kvaser device.

        In single handle mode this blocks the sending of messages for up to 1ms
        before releasing the lock.
        """
        arb_id = ctypes.c_long(0)
        data = ctypes.create_string_buffer(8)
        dlc = ctypes.c_uint(0)
        flags = ctypes.c_uint(0)
        timestamp = ctypes.c_ulong(0)
        timeout = 1000

        if self.single_handle:
            timeout = 1
            self.done_writing.acquire()

            while self.writing_event.is_set():
                # releases the underlying lock, and then blocks until it is awakened
                # by a notify() from the tx thread. Once awakened it re-acquires the lock
                self.done_writing.wait()

        log.log(9, 'Reading for 1ms on handle: %s' % self._read_handle)
        status = canReadWait(
            self._read_handle,
            ctypes.byref(arb_id),
            ctypes.byref(data),
            ctypes.byref(dlc),
            ctypes.byref(flags),
            ctypes.byref(timestamp),
            timeout  # This is an X ms blocking read
        )
        if self.single_handle:
            # Don't want to keep the done_writing condition's Lock
            self.done_writing.release()

        if status == canstat.canOK:
            log.debug('read complete -> status OK')
            data_array = list(map(ord, data))
            is_extended = int(flags.value) & canstat.canMSG_EXT
            msg_timestamp = self.__convert_timestamp(timestamp.value)
            rx_msg = Message(arbitration_id=arb_id.value,
                             data=data_array[:dlc.value],
                             dlc=dlc.value,
                             extended_id=is_extended,
                             timestamp=msg_timestamp)
            log.info('Got message: %s' % rx_msg)
            return rx_msg
        else:
            log.debug('read complete -> status not okay')

    def send(self, tx_msg):
        #log.debug("Writing a message: {}".format(tx_msg))
        ArrayConstructor = ctypes.c_byte * tx_msg.dlc
        buf = ArrayConstructor(*tx_msg.data)
        canWriteWait(self._write_handle,
                     tx_msg.arbitration_id,
                     ctypes.byref(buf),
                     tx_msg.dlc,
                     tx_msg.flags,
                     5)

    def shutdown(self):
        self.__threads_running = False
        canBusOff(self._write_handle)
        canClose(self._write_handle)


init_kvaser_library()

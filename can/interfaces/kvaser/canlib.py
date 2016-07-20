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
import ctypes

log = logging.getLogger('can.canlib')
log.setLevel(logging.INFO)

from can import CanError, BusABC
from can import Message
from can.interfaces.kvaser import constants as canstat


# Resolution in us
TIMESTAMP_RESOLUTION = 10


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
        log.debug('"%s" found in library', func_name)
    except AttributeError:
        log.warning('"%s" was not found in library', func_name)
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


canGetChannelData = __get_canlib_function("canGetChannelData",
                                          argtypes=[ctypes.c_int,
                                                    ctypes.c_int,
                                                    ctypes.c_void_p,
                                                    ctypes.c_size_t],
                                          restype=canstat.c_canStatus,
                                          errcheck=__check_status)


DRIVER_MODE_SILENT = False
DRIVER_MODE_NORMAL = True


BITRATE_OBJS = {1000000 : canstat.canBITRATE_1M,
                 500000 : canstat.canBITRATE_500K,
                 250000 : canstat.canBITRATE_250K,
                 125000 : canstat.canBITRATE_125K,
                 100000 : canstat.canBITRATE_100K,
                  83000 : canstat.canBITRATE_83K,
                  62000 : canstat.canBITRATE_62K,
                  50000 : canstat.canBITRATE_50K,
                  10000 : canstat.canBITRATE_10K}


class KvaserBus(BusABC):
    """
    The CAN Bus implemented for the Kvaser interface.
    """

    def __init__(self, channel, can_filters=None, **config):
        """
        :param int channel:
            The Channel id to create this bus with.

        :param list can_filters:
            A list of dictionaries each containing a "can_id" and a "can_mask".

            >>> [{"can_id": 0x11, "can_mask": 0x21}]


        Backend Configuration

        :param int bitrate:
            Bitrate of channel in bit/s
        :param int tseg1:
            Time segment 1, that is, the number of quanta from (but not including)
            the Sync Segment to the sampling point.
            If this parameter is not given, the Kvaser driver will try to choose
            all bit timing parameters from a set of defaults.
        :param int tseg2:
            Time segment 2, that is, the number of quanta from the sampling
            point to the end of the bit.
        :param int sjw:
            The Synchronisation Jump Width. Decides the maximum number of time quanta
            that the controller can resynchronise every bit.
        :param int no_samp:
            Either 1 or 3. Some CAN controllers can also sample each bit three times.
            In this case, the bit will be sampled three quanta in a row,
            with the last sample being taken in the edge between TSEG1 and TSEG2.
            Three samples should only be used for relatively slow baudrates.

        :param bool driver_mode:
            Silent or normal.

        :param bool single_handle:
            Use one Kvaser CANLIB bus handle for both reading and writing. Note recv
            timeouts will be ignored in single handle mode.
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

        try:
            channel = int(channel)
        except ValueError:
            raise ValueError('channel must be an integer')

        if 'tseg1' not in config and bitrate in BITRATE_OBJS:
            bitrate = BITRATE_OBJS[bitrate]

        log.debug('Initialising bus instance')
        self.single_handle = single_handle

        num_channels = ctypes.c_int(0)
        res = canGetNumberOfChannels(ctypes.byref(num_channels))
        log.debug("Res: {}".format(res))
        num_channels = int(num_channels.value)
        log.info('Found %d available channels' % num_channels)

        log.debug('Creating read handle to bus channel: %s' % channel)
        self._read_handle = canOpenChannel(channel, canstat.canOPEN_ACCEPT_VIRTUAL)
        canIoCtl(self._read_handle,
                 canstat.canIOCTL_SET_TIMER_SCALE,
                 ctypes.byref(ctypes.c_long(TIMESTAMP_RESOLUTION)),
                 4)
        canSetBusParams(self._read_handle, bitrate, tseg1, tseg2, sjw, no_samp, 0)

        if can_filters is not None and len(can_filters):
            log.info("The kvaser canlib backend is filtering messages")
            code, mask = 0, 0
            for can_filter in can_filters:
                code |= can_filter['can_id']
                mask |= can_filter['can_mask']
            log.info("Filtering on: {}  {}".format(code, mask))
            canSetAcceptanceFilter(self._read_handle, code, mask, 1)

        if self.single_handle:
            log.debug("We don't require separate handles to the bus")
            self._write_handle = self._read_handle
        else:
            log.debug('Creating separate handle for TX on channel: %s' % channel)
            self._write_handle = canOpenChannel(channel, canstat.canOPEN_ACCEPT_VIRTUAL)
            canBusOn(self._read_handle)

        can_driver_mode = canstat.canDRIVER_SILENT if driver_mode == DRIVER_MODE_SILENT else canstat.canDRIVER_NORMAL
        canSetBusOutputControl(self._write_handle, can_driver_mode)
        log.debug('Going bus on TX handle')
        canBusOn(self._write_handle)

        self.channel_info = self.get_channel_info()

        self.timer_offset = None  # Used to zero the timestamps from the first message

        '''
        Approximate offset between time.time() and CAN timestamps (~2ms accuracy)
        There will always be some lag between when the message is on the bus to
        when it reaches Python. Allow messages to be on the bus for a while before
        reading this value so it has a chance to correct itself
        '''
        self.pc_time_offset = None

        super(KvaserBus, self).__init__()

    def get_channel_info(self):
        name = ctypes.create_string_buffer(80)
        canGetChannelData(self._write_handle,
                          canstat.canCHANNELDATA_DEVDESCR_ASCII,
                          ctypes.byref(name), ctypes.sizeof(name))
        buf_type = ctypes.c_uint * 1
        buf = buf_type()
        canGetChannelData(self._write_handle,
                          canstat.canCHANNELDATA_CHAN_NO_ON_CARD,
                          ctypes.byref(buf), ctypes.sizeof(buf))
        return '%s (channel %d)' % (name.value.decode(), buf[0])

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

        timestamp = float(value - self.timer_offset) / (1000000 / TIMESTAMP_RESOLUTION)  # Convert into seconds
        timestamp += self.pc_time_offset
        lag = time.time() - timestamp
        if lag < 0:
            # If we see a timestamp that is quicker than the ever before, update the offset
            self.pc_time_offset += lag
        return timestamp

    def recv(self, timeout=None):
        """
        Read a message from kvaser device.
        """
        arb_id = ctypes.c_long(0)
        data = ctypes.create_string_buffer(8)
        dlc = ctypes.c_uint(0)
        flags = ctypes.c_uint(0)
        timestamp = ctypes.c_ulong(0)
        timeout = int(timeout * 1000) if timeout else 0

        log.log(9, 'Reading for %d ms on handle: %s' % (timeout, self._read_handle))
        status = canReadWait(
            self._read_handle,
            ctypes.byref(arb_id),
            ctypes.byref(data),
            ctypes.byref(dlc),
            ctypes.byref(flags),
            ctypes.byref(timestamp),
            timeout  # This is an X ms blocking read
        )

        if status == canstat.canOK:
            log.debug('read complete -> status OK')
            data_array = data.raw
            flags = flags.value
            is_extended = bool(flags & canstat.canMSG_EXT)
            is_remote_frame = bool(flags & canstat.canMSG_RTR)
            is_error_frame = bool(flags & canstat.canMSG_ERROR_FRAME)
            msg_timestamp = self.__convert_timestamp(timestamp.value)
            rx_msg = Message(arbitration_id=arb_id.value,
                             data=data_array[:dlc.value],
                             dlc=dlc.value,
                             extended_id=is_extended,
                             is_error_frame=is_error_frame,
                             is_remote_frame=is_remote_frame,
                             timestamp=msg_timestamp)
            rx_msg.flags = flags
            rx_msg.raw_timestamp = timestamp.value
            log.debug('Got message: %s' % rx_msg)
            return rx_msg
        else:
            log.debug('read complete -> status not okay')
            return None

    def send(self, msg):
        #log.debug("Writing a message: {}".format(msg))
        flags = 0
        if msg.id_type:
            flags |= canstat.canMSG_EXT
        if msg.is_remote_frame:
            flags |= canstat.canMSG_RTR
        if msg.is_error_frame:
            flags |= canstat.canMSG_ERROR_FRAME
        ArrayConstructor = ctypes.c_byte * msg.dlc
        buf = ArrayConstructor(*msg.data)
        canWriteWait(self._write_handle,
                     msg.arbitration_id,
                     ctypes.byref(buf),
                     msg.dlc,
                     flags,
                     5)

    def shutdown(self):
        canBusOff(self._write_handle)
        canClose(self._write_handle)


init_kvaser_library()

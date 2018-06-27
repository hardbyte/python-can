#!/usr/bin/env python
# coding: utf-8

"""
Contains Python equivalents of the function and constant
definitions in CANLIB's canlib.h, with some supporting functionality
specific to Python.

Copyright (C) 2010 Dynamic Controls
"""

from __future__ import absolute_import

import sys
import time
import logging
import ctypes

from can import CanError, BusABC
from can import Message
from . import constants as canstat

log = logging.getLogger('can.kvaser')

# Resolution in us
TIMESTAMP_RESOLUTION = 10

TIMESTAMP_FACTOR = TIMESTAMP_RESOLUTION / 1000000.0


try:
    if sys.platform == "win32":
        __canlib = ctypes.windll.LoadLibrary("canlib32")
    else:
        __canlib = ctypes.cdll.LoadLibrary("libcanlib.so")
    log.info("loaded kvaser's CAN library")
except OSError:
    log.warning("Kvaser canlib is unavailable.")
    __canlib = None


def _unimplemented_function(*args):
    raise NotImplementedError('This function is not implemented in canlib')


def __get_canlib_function(func_name, argtypes=[], restype=None, errcheck=None):
    #log.debug('Wrapping function "%s"' % func_name)
    try:
        # e.g. canlib.canBusOn
        retval = getattr(__canlib, func_name)
        #log.debug('"%s" found in library', func_name)
    except AttributeError:
        log.warning('"%s" was not found in library', func_name)
        return _unimplemented_function
    else:
        #log.debug('Result type is: %s' % type(restype))
        #log.debug('Error check function is: %s' % errcheck)
        retval.argtypes = argtypes
        retval.restype = restype
        if errcheck:
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
        return "Function %s failed - %s" % (self.function.__name__,
                                            self.__get_error_message())

    def __get_error_message(self):
        errmsg = ctypes.create_string_buffer(128)
        canGetErrorText(self.error_code, errmsg, len(errmsg))
        return errmsg.value.decode("ascii")


def __convert_can_status_to_int(result):
    #log.debug("converting can status to int {} ({})".format(result, type(result)))
    if isinstance(result, int):
        return result
    else:
        return result.value


def __check_status(result, function, arguments):
    result = __convert_can_status_to_int(result)
    if not canstat.CANSTATUS_SUCCESS(result):
        #log.debug('Detected error while checking CAN status')
        raise CANLIBError(function, result, arguments)
    return result


def __check_status_read(result, function, arguments):
    result = __convert_can_status_to_int(result)
    if not canstat.CANSTATUS_SUCCESS(result) and result != canstat.canERR_NOMSG:
        #log.debug('Detected error in which checking status read')
        raise CANLIBError(function, result, arguments)
    return result


class c_canHandle(ctypes.c_int):
    pass

canINVALID_HANDLE = -1


def __handle_is_valid(handle):
    return (handle.value > canINVALID_HANDLE)


def __check_bus_handle_validity(handle, function, arguments):
    if not __handle_is_valid(handle):
        result = __convert_can_status_to_int(handle)
        raise CANLIBError(function, result, arguments)
    else:
        return handle

if __canlib is not None:
    canInitializeLibrary = __get_canlib_function("canInitializeLibrary")

    canGetErrorText = __get_canlib_function("canGetErrorText",
                                            argtypes=[canstat.c_canStatus, ctypes.c_char_p, ctypes.c_uint],
                                            restype=canstat.c_canStatus,
                                            errcheck=__check_status)

    # TODO wrap this type of function to provide a more Pythonic API
    canGetNumberOfChannels = __get_canlib_function("canGetNumberOfChannels",
                                                   argtypes=[ctypes.c_void_p],
                                                   restype=canstat.c_canStatus,
                                                   errcheck=__check_status)

    kvReadTimer = __get_canlib_function("kvReadTimer",
                                        argtypes=[c_canHandle,
                                                  ctypes.POINTER(ctypes.c_uint)],
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

    canSetBusParamsFd = __get_canlib_function("canSetBusParamsFd",
                                            argtypes=[c_canHandle, ctypes.c_long,
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

    canWrite = __get_canlib_function("canWrite",
                                     argtypes=[
                                         c_canHandle,
                                         ctypes.c_long,
                                         ctypes.c_void_p,
                                         ctypes.c_uint,
                                         ctypes.c_uint],
                                     restype=canstat.c_canStatus,
                                     errcheck=__check_status)

    canWriteSync = __get_canlib_function("canWriteSync",
                                         argtypes=[c_canHandle, ctypes.c_ulong],
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

    kvFlashLeds = __get_canlib_function("kvFlashLeds",
                                        argtypes=[c_canHandle, ctypes.c_int,
                                                  ctypes.c_int],
                                        restype=ctypes.c_short,
                                        errcheck=__check_status)

    if sys.platform == "win32":
        canGetVersionEx = __get_canlib_function("canGetVersionEx",
                                                argtypes=[ctypes.c_uint],
                                                restype=ctypes.c_uint,
                                                errcheck=__check_status)

    canGetChannelData = __get_canlib_function("canGetChannelData",
                                          argtypes=[ctypes.c_int,
                                                    ctypes.c_int,
                                                    ctypes.c_void_p,
                                                    ctypes.c_size_t],
                                          restype=canstat.c_canStatus,
                                          errcheck=__check_status)


def init_kvaser_library():
    if __canlib is not None:
        try:
            log.debug("Initializing Kvaser CAN library")
            canInitializeLibrary()
            log.debug("CAN library initialized")
        except:
            log.warning("Kvaser canlib could not be initialized.")


DRIVER_MODE_SILENT = False
DRIVER_MODE_NORMAL = True


BITRATE_OBJS = {
    1000000: canstat.canBITRATE_1M,
    500000: canstat.canBITRATE_500K,
    250000: canstat.canBITRATE_250K,
    125000: canstat.canBITRATE_125K,
    100000: canstat.canBITRATE_100K,
    83000: canstat.canBITRATE_83K,
    62000: canstat.canBITRATE_62K,
    50000: canstat.canBITRATE_50K,
    10000: canstat.canBITRATE_10K
}

BITRATE_FD = {
    500000: canstat.canFD_BITRATE_500K_80P,
    1000000: canstat.canFD_BITRATE_1M_80P,
    2000000: canstat.canFD_BITRATE_2M_80P,
    4000000: canstat.canFD_BITRATE_4M_80P,
    8000000: canstat.canFD_BITRATE_8M_60P
}


class KvaserBus(BusABC):
    """
    The CAN Bus implemented for the Kvaser interface.
    """

    def __init__(self, channel, can_filters=None, **config):
        """
        :param int channel:
            The Channel id to create this bus with.

        :param list can_filters:
            See :meth:`can.BusABC.set_filters`.

        Backend Configuration

        :param int bitrate:
            Bitrate of channel in bit/s
        :param bool accept_virtual:
            If virtual channels should be accepted.
        :param int tseg1:
            Time segment 1, that is, the number of quanta from (but not including)
            the Sync Segment to the sampling point.
            If this parameter is not given, the Kvaser driver will try to choose
            all bit timing parameters from a set of defaults.
        :param int tseg2:
            Time segment 2, that is, the number of quanta from the sampling
            point to the end of the bit.
        :param int sjw:
            The Synchronization Jump Width. Decides the maximum number of time quanta
            that the controller can resynchronize every bit.
        :param int no_samp:
            Either 1 or 3. Some CAN controllers can also sample each bit three times.
            In this case, the bit will be sampled three quanta in a row,
            with the last sample being taken in the edge between TSEG1 and TSEG2.
            Three samples should only be used for relatively slow baudrates.

        :param bool driver_mode:
            Silent or normal.

        :param bool single_handle:
            Use one Kvaser CANLIB bus handle for both reading and writing.
            This can be set if reading and/or writing is done from one thread.
        :param bool receive_own_messages:
            If messages transmitted should also be received back.
            Only works if single_handle is also False.
            If you want to receive messages from other applications on the same
            computer, set this to True or set single_handle to True.
        :param bool fd:
            If CAN-FD frames should be supported.
        :param int data_bitrate:
            Which bitrate to use for data phase in CAN FD.
            Defaults to arbitration bitrate.

        """

        log.info("CAN Filters: {}".format(can_filters))
        log.info("Got configuration of: {}".format(config))
        bitrate = config.get('bitrate', 500000)
        tseg1 = config.get('tseg1', 0)
        tseg2 = config.get('tseg2', 0)
        sjw = config.get('sjw', 0)
        no_samp = config.get('no_samp', 0)
        driver_mode = config.get('driver_mode', DRIVER_MODE_NORMAL)
        single_handle = config.get('single_handle', False)
        receive_own_messages = config.get('receive_own_messages', False)
        accept_virtual = config.get('accept_virtual', True)
        fd = config.get('fd', False)
        data_bitrate = config.get('data_bitrate', None)

        try:
            channel = int(channel)
        except ValueError:
            raise ValueError('channel must be an integer')
        self.channel = channel

        log.debug('Initialising bus instance')
        self.single_handle = single_handle

        num_channels = ctypes.c_int(0)
        res = canGetNumberOfChannels(ctypes.byref(num_channels))
        #log.debug("Res: {}".format(res))
        num_channels = int(num_channels.value)
        log.info('Found %d available channels' % num_channels)
        for idx in range(num_channels):
            channel_info = get_channel_info(idx)
            log.info('%d: %s', idx, channel_info)
            if idx == channel:
                self.channel_info = channel_info

        flags = 0
        if accept_virtual:
            flags |= canstat.canOPEN_ACCEPT_VIRTUAL
        if fd:
            flags |= canstat.canOPEN_CAN_FD

        log.debug('Creating read handle to bus channel: %s' % channel)
        self._read_handle = canOpenChannel(channel, flags)
        canIoCtl(self._read_handle,
                 canstat.canIOCTL_SET_TIMER_SCALE,
                 ctypes.byref(ctypes.c_long(TIMESTAMP_RESOLUTION)),
                 4)
        
        if fd:
            if 'tseg1' not in config and bitrate in BITRATE_FD:
                # Use predefined bitrate for arbitration
                bitrate = BITRATE_FD[bitrate]
            if data_bitrate in BITRATE_FD:
                # Use predefined bitrate for data
                data_bitrate = BITRATE_FD[data_bitrate]
            elif not data_bitrate:
                # Use same bitrate for arbitration and data phase
                data_bitrate = bitrate
            canSetBusParamsFd(self._read_handle, bitrate, tseg1, tseg2, sjw)
        else:
            if 'tseg1' not in config and bitrate in BITRATE_OBJS:
                bitrate = BITRATE_OBJS[bitrate]
        canSetBusParams(self._read_handle, bitrate, tseg1, tseg2, sjw, no_samp, 0)

        # By default, use local echo if single handle is used (see #160)
        local_echo = single_handle or receive_own_messages
        if receive_own_messages and single_handle:
            log.warning("receive_own_messages only works if single_handle is False")
        canIoCtl(self._read_handle,
                 canstat.canIOCTL_SET_LOCAL_TXECHO,
                 ctypes.byref(ctypes.c_byte(local_echo)),
                 1)

        if self.single_handle:
            log.debug("We don't require separate handles to the bus")
            self._write_handle = self._read_handle
        else:
            log.debug('Creating separate handle for TX on channel: %s' % channel)
            self._write_handle = canOpenChannel(channel, flags)
            canBusOn(self._read_handle)

        can_driver_mode = canstat.canDRIVER_SILENT if driver_mode == DRIVER_MODE_SILENT else canstat.canDRIVER_NORMAL
        canSetBusOutputControl(self._write_handle, can_driver_mode)
        log.debug('Going bus on TX handle')
        canBusOn(self._write_handle)

        timer = ctypes.c_uint(0)
        try:
            kvReadTimer(self._read_handle, ctypes.byref(timer))
        except Exception as exc:
            # timer is usually close to 0
            log.info(str(exc))
        self._timestamp_offset = time.time() - (timer.value * TIMESTAMP_FACTOR)

        self._is_filtered = False
        super(KvaserBus, self).__init__(channel=channel, can_filters=can_filters, **config)

    def _apply_filters(self, filters):
        if filters and len(filters) == 1:
            can_id = filters[0]['can_id']
            can_mask = filters[0]['can_mask']
            extended = 1 if filters[0].get('extended') else 0
            try:
                for handle in (self._read_handle, self._write_handle):
                    canSetAcceptanceFilter(handle, can_id, can_mask, extended)
            except (NotImplementedError, CANLIBError) as e:
                self._is_filtered = False
                log.error('Filtering is not supported - %s', e)
            else:
                self._is_filtered = True
                log.info('canlib is filtering on ID 0x%X, mask 0x%X', can_id, can_mask)

        else:
            self._is_filtered = False
            log.info('Hardware filtering has been disabled')
            try:
                for handle in (self._read_handle, self._write_handle):
                    for extended in (0, 1):
                        canSetAcceptanceFilter(handle, 0, 0, extended)
            except (NotImplementedError, CANLIBError):
                # TODO add logging?
                pass

    def flush_tx_buffer(self):
        """ Wipeout the transmit buffer on the Kvaser.
        """
        canIoCtl(self._write_handle, canstat.canIOCTL_FLUSH_TX_BUFFER, 0, 0)

    def _recv_internal(self, timeout=None):
        """
        Read a message from kvaser device and return whether filtering has taken place.
        """
        arb_id = ctypes.c_long(0)
        data = ctypes.create_string_buffer(64)
        dlc = ctypes.c_uint(0)
        flags = ctypes.c_uint(0)
        timestamp = ctypes.c_ulong(0)

        if timeout is None:
            # Set infinite timeout
            # http://www.kvaser.com/canlib-webhelp/group___c_a_n.html#ga2edd785a87cc16b49ece8969cad71e5b
            timeout = 0xFFFFFFFF
        else:
            timeout = int(timeout * 1000)

        #log.log(9, 'Reading for %d ms on handle: %s' % (timeout, self._read_handle))
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
            #log.debug('read complete -> status OK')
            data_array = data.raw
            flags = flags.value
            is_extended = bool(flags & canstat.canMSG_EXT)
            is_remote_frame = bool(flags & canstat.canMSG_RTR)
            is_error_frame = bool(flags & canstat.canMSG_ERROR_FRAME)
            is_fd = bool(flags & canstat.canFDMSG_FDF)
            bitrate_switch = bool(flags & canstat.canFDMSG_BRS)
            error_state_indicator = bool(flags & canstat.canFDMSG_ESI)
            msg_timestamp = timestamp.value * TIMESTAMP_FACTOR
            rx_msg = Message(arbitration_id=arb_id.value,
                             data=data_array[:dlc.value],
                             dlc=dlc.value,
                             extended_id=is_extended,
                             is_error_frame=is_error_frame,
                             is_remote_frame=is_remote_frame,
                             is_fd=is_fd,
                             bitrate_switch=bitrate_switch,
                             error_state_indicator=error_state_indicator,
                             channel=self.channel,
                             timestamp=msg_timestamp + self._timestamp_offset)
            rx_msg.flags = flags
            rx_msg.raw_timestamp = msg_timestamp
            #log.debug('Got message: %s' % rx_msg)
            return rx_msg, self._is_filtered
        else:
            #log.debug('read complete -> status not okay')
            return None, self._is_filtered

    def send(self, msg, timeout=None):
        #log.debug("Writing a message: {}".format(msg))
        flags = canstat.canMSG_EXT if msg.id_type else canstat.canMSG_STD
        if msg.is_remote_frame:
            flags |= canstat.canMSG_RTR
        if msg.is_error_frame:
            flags |= canstat.canMSG_ERROR_FRAME
        if msg.is_fd:
            flags |= canstat.canFDMSG_FDF
        if msg.bitrate_switch:
            flags |= canstat.canFDMSG_BRS
        ArrayConstructor = ctypes.c_byte * msg.dlc
        buf = ArrayConstructor(*msg.data)
        canWrite(self._write_handle,
                 msg.arbitration_id,
                 ctypes.byref(buf),
                 msg.dlc,
                 flags)
        if timeout:
            canWriteSync(self._write_handle, int(timeout * 1000))

    def flash(self, flash=True):
        """
        Turn on or off flashing of the device's LED for physical
        identification purposes.
        """
        if flash:
            action = canstat.kvLED_ACTION_ALL_LEDS_ON
        else:
            action = canstat.kvLED_ACTION_ALL_LEDS_OFF

        try:
            kvFlashLeds(self._read_handle, action, 30000)
        except (CANLIBError, NotImplementedError) as e:
            log.error('Could not flash LEDs (%s)', e)

    def shutdown(self):
        # Wait for transmit queue to be cleared
        try:
            canWriteSync(self._write_handle, 100)
        except CANLIBError:
            # Not a huge deal and it seems that we get timeout if no messages
            # exists in the buffer at all
            pass
        if not self.single_handle:
            canBusOff(self._read_handle)
            canClose(self._read_handle)
        canBusOff(self._write_handle)
        canClose(self._write_handle)

    @staticmethod
    def _detect_available_configs():
        num_channels = ctypes.c_int(0)
        try:
            canGetNumberOfChannels(ctypes.byref(num_channels))
        except Exception:
            pass
        return [
            {'interface': 'kvaser', 'channel': channel}
            for channel in range(num_channels.value)
        ]


def get_channel_info(channel):
    name = ctypes.create_string_buffer(80)
    serial = ctypes.c_uint64()
    number = ctypes.c_uint()

    canGetChannelData(channel,
                      canstat.canCHANNELDATA_DEVDESCR_ASCII,
                      ctypes.byref(name), ctypes.sizeof(name))
    canGetChannelData(channel,
                      canstat.canCHANNELDATA_CARD_SERIAL_NO,
                      ctypes.byref(serial), ctypes.sizeof(serial))
    canGetChannelData(channel,
                      canstat.canCHANNELDATA_CHAN_NO_ON_CARD,
                      ctypes.byref(number), ctypes.sizeof(number))

    return '%s, S/N %d (#%d)' % (
        name.value.decode("ascii"), serial.value, number.value + 1)


init_kvaser_library()

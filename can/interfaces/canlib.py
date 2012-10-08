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
import platform
import threading
import Queue as queue
import ctypes

log = logging.getLogger('CANLIB')
log.setLevel(logging.WARNING)

from .. import CANError
import canlib_constants as canstat
from ..bus import BusABC
from ..message import Message
from ..constants import *

if sys.platform == "win32":
    __canlib = ctypes.windll.LoadLibrary("canlib32")
else:
    __canlib = ctypes.cdll.LoadLibrary("libcanlib.so")



def __get_canlib_function(func_name, argtypes=None, restype=None, errcheck=None):
    log.debug('Wrapping function "%s"' % func_name)
    try:
        retval = getattr(__canlib, func_name)# e.g. canlib.canBusOn
        log.debug('Function found in library')
    except AttributeError:
        logging.warning('Function not found in library')
    else:
        log.debug('Result type is: %s' % type(restype))
        log.debug('Error check function is: %s' % errcheck)
        retval.argtypes = argtypes
        retval.restype = restype
        retval.errcheck = errcheck
        return retval


class CANLIBError(CANError):

    def __init__(self, function, error_code, arguments):
        Exception.__init__(self)
        self.error_code = error_code
        self.function = function
        self.arguments = arguments

    def __str__(self):
        return "function %s failed - %s - arguments were %s" % (self.function.__name__, self.__get_error_message(), self.arguments)

    def __get_error_message(self):
        errmsg = ctypes.create_string_buffer(128)
        canGetErrorText(self.error_code, errmsg, len(errmsg))
        return "%s (code %d)" % (errmsg.value, self.error_code)

class ChannelNotFoundError(CANLIBError):
    pass


class Message(Message):
    def __init__(self, *args, **kwargs):
        super(Message, self).__init__(*args, **kwargs)
        self.flags = 0
        self.flags &= (0xFFFF - canstat.canMSG_RTR)
        self.flags |= (self.is_remote_frame * canstat.canMSG_RTR)
        self.flags &= (0xFFFF - canstat.canMSG_WAKEUP)
        if self.is_wakeup:
            self.flags |= canstat.canMSG_WAKEUP
        self.flags &= (0xFFFF - canstat.canMSG_ERROR_FRAME)
        if self.is_error_frame:
            self.flags |= canstat.canMSG_ERROR_FRAME


def __convert_can_status_to_int(result):
    if isinstance(result, (int, long)):
        _result = result
    else:
        _result = result.value
    return _result

def __check_status(result, function, arguments):
    _result = __convert_can_status_to_int(result)
    if not canstat.CANSTATUS_SUCCESS(_result):
        log.debug('Detected error while checking CAN status')
        raise CANLIBError(function, _result, arguments)
    else:
        return result

def __check_status_read(result, function, arguments):
    _result = __convert_can_status_to_int(result)
    if not canstat.CANSTATUS_SUCCESS(_result) and (_result != canstat.canERR_NOMSG):
        log.debug('Detected error in __check_status_read')
        raise CANLIBError(function, _result, arguments)
    else:
        return result

class c_canHandle(ctypes.c_int):
    pass

canINVALID_HANDLE = -1

def __handle_is_valid(handle):
    return (handle > canINVALID_HANDLE)

def __check_bus_handle_validity(handle, function, arguments):
    if not __handle_is_valid(handle):
        raise CANLIBError(function, handle, arguments)
    else:
        return handle

canInitializeLibrary = __get_canlib_function("canInitializeLibrary", argtypes=[], restype=canstat.c_canStatus, errcheck=__check_status)

canGetErrorText = __get_canlib_function("canGetErrorText", argtypes=[canstat.c_canStatus, ctypes.c_char_p, ctypes.c_uint], restype=canstat.c_canStatus, errcheck=__check_status)

canGetNumberOfChannels = __get_canlib_function("canGetNumberOfChannels", argtypes=[ctypes.c_void_p], restype=canstat.c_canStatus, errcheck=__check_status)

if sys.platform == "win32":
    __canReadTimer_func_name = "kvReadTimer"
else:
    __canReadTimer_func_name = "canReadTimer"
canReadTimer = __get_canlib_function(__canReadTimer_func_name, argtypes=[c_canHandle, ctypes.c_void_p], restype=canstat.c_canStatus, errcheck=__check_status)

canBusOff = __get_canlib_function("canBusOff", argtypes=[c_canHandle], restype=canstat.c_canStatus, errcheck=__check_status)

canBusOn = __get_canlib_function("canBusOn", argtypes=[c_canHandle], restype=canstat.c_canStatus, errcheck=__check_status)

canClose = __get_canlib_function("canClose", argtypes=[c_canHandle], restype=canstat.c_canStatus, errcheck=__check_status)

canOPEN_EXCLUSIVE = 0x0008
canOPEN_REQUIRE_EXTENDED = 0x0010
canOPEN_ACCEPT_VIRTUAL = 0x0020
canOPEN_OVERRIDE_EXCLUSIVE = 0x0040
canOPEN_REQUIRE_INIT_ACCESS = 0x0080
canOPEN_NO_INIT_ACCESS = 0x0100
canOPEN_ACCEPT_LARGE_DLC = 0x0200
FLAGS_MASK = (canOPEN_EXCLUSIVE | canOPEN_REQUIRE_EXTENDED | canOPEN_ACCEPT_VIRTUAL | canOPEN_OVERRIDE_EXCLUSIVE | canOPEN_REQUIRE_INIT_ACCESS | canOPEN_NO_INIT_ACCESS | canOPEN_ACCEPT_LARGE_DLC)
canOpenChannel = __get_canlib_function("canOpenChannel", argtypes=[ctypes.c_int, ctypes.c_int], restype=c_canHandle, errcheck=__check_bus_handle_validity)

canSetBusParams = __get_canlib_function("canSetBusParams", argtypes=[c_canHandle, ctypes.c_long, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint], restype=canstat.c_canStatus, errcheck=__check_status)

canDRIVER_NORMAL = 4
canDRIVER_SILENT = 1
canDRIVER_SELFRECEPTION = 8
canDRIVER_OFF = 0
canSetBusOutputControl = __get_canlib_function("canSetBusOutputControl", argtypes=[c_canHandle, ctypes.c_uint], restype=canstat.c_canStatus, errcheck=__check_status)

canReadWait = __get_canlib_function("canReadWait", argtypes=[c_canHandle, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_long], restype=canstat.c_canStatus, errcheck=__check_status_read)

canWriteWait = __get_canlib_function("canWriteWait", argtypes=[c_canHandle, ctypes.c_long, ctypes.c_void_p, ctypes.c_uint, ctypes.c_uint, ctypes.c_ulong], restype=canstat.c_canStatus, errcheck=__check_status)

canIOCTL_GET_RX_BUFFER_LEVEL = 8
canIOCTL_GET_TX_BUFFER_LEVEL = 9
canIOCTL_FLUSH_RX_BUFFER = 10
canIOCTL_FLUSH_TX_BUFFER = 11
canIOCTL_GET_TIMER_SCALE = 12
canIOCTL_SET_TXRQ = 13
canIOCTL_GET_EVENTHANDLE = 14
canIOCTL_SET_BYPASS_MODE = 15
canIOCTL_SET_WAKEUP = 16
canIOCTL_GET_DRIVERHANDLE = 17
canIOCTL_MAP_RXQUEUE = 18
canIOCTL_GET_WAKEUP = 19
canIOCTL_SET_REPORT_ACCESS_ERRORS = 20
canIOCTL_GET_REPORT_ACCESS_ERRORS = 21
canIOCTL_CONNECT_TO_VIRTUAL_BUS = 22
canIOCTL_DISCONNECT_FROM_VIRTUAL_BUS = 23
canIOCTL_SET_USER_IOPORT = 24
canIOCTL_GET_USER_IOPORT = 25
canIOCTL_SET_BUFFER_WRAPAROUND_MODE = 26
canIOCTL_SET_RX_QUEUE_SIZE = 27
canIOCTL_SET_USB_THROTTLE = 28
canIOCTL_GET_USB_THROTTLE = 29
canIOCTL_SET_BUSON_TIME_AUTO_RESET = 30
canIOCTL_PREFER_EXT = 1
canIOCTL_PREFER_STD = 2
canIOCTL_CLEAR_ERROR_COUNTERS = 5
canIOCTL_SET_TIMER_SCALE = 6
canIOCTL_SET_TXACK = 7
canIoCtl = __get_canlib_function("canIoCtl", argtypes=[c_canHandle, ctypes.c_uint, ctypes.c_void_p, ctypes.c_uint], restype=canstat.c_canStatus, errcheck=__check_status)

canGetVersion = __get_canlib_function("canGetVersion", restype=ctypes.c_short, errcheck=__check_status)
if sys.platform == "win32":
    canGetVersionEx = __get_canlib_function("canGetVersionEx", argtypes=[ctypes.c_uint], restype=ctypes.c_uint, errcheck=__check_status)
    canVERSION_CANLIB32_VERSION = 0
    canVERSION_CANLIB32_PRODVER = 1
    canVERSION_CANLIB32_PRODVER32 = 2
    canVERSION_CANLIB32_BETA = 3

canTRANSCEIVER_TYPE_UNKNOWN = 0
canTRANSCEIVER_TYPE_251 = 1
canTRANSCEIVER_TYPE_252 = 2
canTRANSCEIVER_TYPE_DNOPTO = 3
canTRANSCEIVER_TYPE_W210 = 4
canTRANSCEIVER_TYPE_SWC_PROTO = 5
canTRANSCEIVER_TYPE_SWC = 6
canTRANSCEIVER_TYPE_EVA = 7
canTRANSCEIVER_TYPE_FIBER = 8
canTRANSCEIVER_TYPE_K251 = 9
canTRANSCEIVER_TYPE_K = 10
canTRANSCEIVER_TYPE_1054_OPTO = 11
canTRANSCEIVER_TYPE_SWC_OPTO = 12
canTRANSCEIVER_TYPE_TT = 13
canTRANSCEIVER_TYPE_1050 = 14
canTRANSCEIVER_TYPE_1050_OPTO = 15
canTRANSCEIVER_TYPE_1041 = 16
canTRANSCEIVER_TYPE_1041_OPTO = 17
canTRANSCEIVER_TYPE_RS485 = 18
canTRANSCEIVER_TYPE_LIN = 19
canTRANSCEIVER_TYPE_KONE = 20
canTRANSCEIVER_TYPE_LINX_LIN = 64
canTRANSCEIVER_TYPE_LINX_J1708 = 66
canTRANSCEIVER_TYPE_LINX_K = 68
canTRANSCEIVER_TYPE_LINX_SWC = 70
canTRANSCEIVER_TYPE_LINX_LS = 72

canTransceiverTypeStrings = {
    canTRANSCEIVER_TYPE_UNKNOWN: "unknown",
     canTRANSCEIVER_TYPE_251: "82C251",
     canTRANSCEIVER_TYPE_252: "82C252/TJA1053/TJA1054",
     canTRANSCEIVER_TYPE_DNOPTO: "Optoisolated 82C251",
     canTRANSCEIVER_TYPE_W210: "W210",
     canTRANSCEIVER_TYPE_SWC_PROTO: "AU5790 prototype",
     canTRANSCEIVER_TYPE_SWC: "AU5790",
     canTRANSCEIVER_TYPE_EVA: "EVA",
     canTRANSCEIVER_TYPE_FIBER: "82C251 with fibre extension",
     canTRANSCEIVER_TYPE_K251: "K251",
     canTRANSCEIVER_TYPE_K: "K",
     canTRANSCEIVER_TYPE_1054_OPTO: "TJA1054 optical isolation",
     canTRANSCEIVER_TYPE_SWC_OPTO: "AU5790 optical isolation",
     canTRANSCEIVER_TYPE_TT: "B10011S Truck-And-Trailer",
     canTRANSCEIVER_TYPE_1050: "TJA1050",
     canTRANSCEIVER_TYPE_1050_OPTO: "TJA1050 optical isolation",
     canTRANSCEIVER_TYPE_1041: "TJA1041",
     canTRANSCEIVER_TYPE_1041_OPTO: "TJA1041 optical isolation",
     canTRANSCEIVER_TYPE_RS485: "RS485",
     canTRANSCEIVER_TYPE_LIN: "LIN",
     canTRANSCEIVER_TYPE_KONE: "KONE",
     canTRANSCEIVER_TYPE_LINX_LIN: "LINX_LIN",
     canTRANSCEIVER_TYPE_LINX_J1708: "LINX_J1708",
     canTRANSCEIVER_TYPE_LINX_K: "LINX_K",
     canTRANSCEIVER_TYPE_LINX_SWC: "LINX_SWC",
     canTRANSCEIVER_TYPE_LINX_LS: "LINX_LS"
}

def lookup_transceiver_type(type):
    try:
        return canTransceiverTypeStrings[type]
    except KeyError:
        return "unknown"

canCHANNELDATA_CHANNEL_CAP = 1
canCHANNELDATA_TRANS_CAP = 2
canCHANNELDATA_CHANNEL_FLAGS = 3
canCHANNELDATA_CARD_TYPE = 4
canCHANNELDATA_CARD_NUMBER = 5
canCHANNELDATA_CHAN_NO_ON_CARD = 6
canCHANNELDATA_CARD_SERIAL_NO = 7
canCHANNELDATA_TRANS_SERIAL_NO = 8
canCHANNELDATA_CARD_FIRMWARE_REV = 9
canCHANNELDATA_CARD_HARDWARE_REV = 10
canCHANNELDATA_CARD_UPC_NO = 11
canCHANNELDATA_TRANS_UPC_NO = 12
canCHANNELDATA_CHANNEL_NAME = 13
canCHANNELDATA_DLL_FILE_VERSION = 14
canCHANNELDATA_DLL_PRODUCT_VERSION = 15
canCHANNELDATA_DLL_FILETYPE = 16
canCHANNELDATA_TRANS_TYPE = 17
canCHANNELDATA_DEVICE_PHYSICAL_POSITION = 18
canCHANNELDATA_UI_NUMBER = 19
canCHANNELDATA_TIMESYNC_ENABLED = 20
canCHANNELDATA_DRIVER_FILE_VERSION = 21
canCHANNELDATA_DRIVER_PRODUCT_VERSION = 22
canCHANNELDATA_MFGNAME_UNICODE = 23
canCHANNELDATA_MFGNAME_ASCII = 24
canCHANNELDATA_DEVDESCR_UNICODE = 25
canCHANNELDATA_DEVDESCR_ASCII = 26
canCHANNELDATA_DRIVER_NAME = 27

canGetChannelData = __get_canlib_function("canGetChannelData", 
                                          argtypes=[ctypes.c_int, 
                                                    ctypes.c_int, 
                                                    ctypes.c_void_p, 
                                                    ctypes.c_size_t], 
                                          restype=canstat.c_canStatus, 
                                          errcheck=__check_status)

DRIVER_MODE_SILENT = False
DRIVER_MODE_NORMAL = (not DRIVER_MODE_SILENT)

class Bus(BusABC):
    '''
    The CAN Bus Object.
    '''
    def __init__(self,
                 channel,
                 bitrate,
                 tseg1,
                 tseg2,
                 sjw,
                 no_samp,
                 driver_mode=DRIVER_MODE_NORMAL,
                 single_handle=False):
        '''
        @param channel
            The Channel id to create this bus with.
        @param bitrate
            Bitrate of channel in bit/s
        @param driver_mode
            Silent or normal.
        @param single_handle
            If True the bus is created with one handle shared between both writing and reading.
        @param tseg1
        @param tseg2
        @param sjw
        @param no_samp
        
        '''
        log.debug('Initialising bus instance')
        self.single_handle = single_handle
        num_channels = ctypes.c_int(0)
        canGetNumberOfChannels(ctypes.byref(num_channels))
        num_channels = int(num_channels.value)
        log.debug('Found %d available channels' % num_channels)

        if type(channel) == str:
            _channel = get_canlib_channel_from_url(channel)
            if _channel is None:
                raise ChannelNotFoundError(channel)
        else:
            _channel = channel
        
        if self.single_handle:
            self.writing_event = threading.Event()
            self.done_writing = threading.Condition()

        log.debug('Creating read handle to bus channel: %s' % _channel)
        self.__read_handle = canOpenChannel(_channel, canOPEN_ACCEPT_VIRTUAL)
        canIoCtl(self.__read_handle, canIOCTL_SET_TIMER_SCALE, ctypes.byref(ctypes.c_long(1)), 4)
        canSetBusParams(self.__read_handle, bitrate, tseg1, tseg2, sjw, no_samp, 0)

        '''
        Bit of a hack, on linux using kvvirtualcan module it seems you must read
        and write on separate channels of the same bus.
        '''
        
        if platform.system() == "Linux" and "virtual" in str(self.channel_info).lower():
            log.debug('Detected virtual channel on linux')
            for chan in range(num_channels):
                c = (chan + 1) % num_channels
                channel_info = get_channel_info(c)
                if "virtual" in str(channel_info).lower() and c != _channel:
                    log.info('Creating separate TX handle on channel: %s' % c)
                    self.__write_handle = canOpenChannel(c, canOPEN_ACCEPT_VIRTUAL)
                    log.info('Going bus on RX handle')
                    canBusOn(self.__read_handle)
                    break
        
        if self.single_handle:
            log.debug("We don't require separate handles to the bus")
            self.__write_handle = self.__read_handle
        else:
            log.debug('Creating separate handle for TX on channel: %s' % _channel)
            self.__write_handle = canOpenChannel(_channel, canOPEN_ACCEPT_VIRTUAL)
            canBusOn(self.__read_handle)

        can_driver_mode = canDRIVER_SILENT if driver_mode == DRIVER_MODE_SILENT else canDRIVER_NORMAL
        canSetBusOutputControl(self.__write_handle, can_driver_mode)
        log.debug('Going bus on TX handle')
        canBusOn(self.__write_handle)
        self.listeners = []
        
        self.__tx_queue = queue.Queue(0)
        self.__threads_running = True
        if not driver_mode == DRIVER_MODE_SILENT:
            self.__write_thread = threading.Thread(target=self.__write_process)
            self.__write_thread.daemon = True
            self.__write_thread.start()
        self.__read_thread = threading.Thread(target=self.__read_process)
        self.__read_thread.daemon = True
        self.__read_thread.start()
        self.timer_offset = None # Used to zero the timestamps from the first message
        
        '''
        Approximate offset between time.time() and CAN timestamps (~2ms accuracy)
        There will always be some lag between when the message is on the bus to 
        when it reaches python. Allow messages to be on the bus for a while before
        reading this value so it has a chance to correct itself'''
        self.pc_time_offset = None

    def flush_tx_buffer(self):
        '''
        Flushes the transmit buffer on the Kvaser
        '''
        canIoCtl(self.__write_handle, canIOCTL_FLUSH_TX_BUFFER, 0, 0)
    
    def __convert_timestamp(self, value):
        # Use the current value if the offset has not been set yet
        if not hasattr(self, 'timer_offset') or self.timer_offset is None: 
            self.timer_offset = value
            self.pc_time_offset = time.time()
        
        if value < self.timer_offset: # Check for overflow
            MAX_32BIT = 0xFFFFFFFF # The maximum value that the timer reaches on a 32-bit machine
            MAX_64BIT = 0x9FFFFFFFF # The maximum value that the timer reaches on a 64-bit machine
            if ctypes.sizeof(ctypes.c_long) == 8:
                value += MAX_64BIT
            elif ctypes.sizeof(ctypes.c_long) == 4:
                value += MAX_32BIT
            else:
                assert False, 'Unknown platform. Expected a long to be 4 or 8 bytes long but it was %i bytes.' % ctypes.sizeof(ctypes.c_long)
            assert value > self.timer_offset, 'CAN Timestamp overflowed. The timer offset was ' + str(self.timer_offset) 
        
        timestamp = (float(value - self.timer_offset) / 1000000) # Convert from us into seconds
        lag = (time.time() - self.pc_time_offset) - timestamp 
        if lag < 0: # If we see a timestamp that is quicker than the ever before, update the offset
            self.pc_time_offset += lag
        return timestamp

    def __read_process(self):
        """
        The consumer thread.
        """
        log.info('Read process starting in canlib')
        while self.__threads_running:
            rx_msg = self.__get_message()
            if rx_msg is not None:
                for listener in self.listeners:
                    listener.on_message_received(rx_msg)

    def __get_message(self):
        '''
        Read a message from kvaiser device.
        
        In single handle mode this blocks the sending of messages for up to 1ms
        before releasing the lock.
        '''
        arb_id = ctypes.c_long(0)
        data = ctypes.create_string_buffer(8)
        dlc = ctypes.c_uint(0)
        flags = ctypes.c_uint(0)
        timestamp = ctypes.c_ulong(0)
        
        if self.single_handle:
            
            self.done_writing.acquire()
            
            while self.writing_event.is_set():
                # releases the underlying lock, and then blocks until it is awakened 
                # by a notify() from the tx thread. Once awakened it re-acquires the lock
                self.done_writing.wait()

        #log.debug('Reading for 1ms on handle: %s' % self.__read_handle)
        status = canReadWait(self.__read_handle, 
                                     ctypes.byref(arb_id), 
                                     ctypes.byref(data), 
                                     ctypes.byref(dlc), 
                                     ctypes.byref(flags), 
                                     ctypes.byref(timestamp),
                                     1  # This is a 1 ms blocking read
                                     )
        if self.single_handle:
            # Don't want to keep the done_writing condition's Lock
            self.done_writing.release()

        
        if status.value == canstat.canOK:
            #log.log(9, 'read complete -> status OK')
            data_array = map(ord, data)
            is_extended = int(flags.value) & canstat.canMSG_EXT
            msg_timestamp = self.__convert_timestamp(timestamp.value)
            rx_msg = Message(arbitration_id=arb_id.value, 
                             data=data_array[:dlc.value],
                             dlc=int(dlc.value), 
                             extended_id=is_extended, 
                             timestamp=msg_timestamp)
            rx_msg.flags = int(flags.value) & canstat.canMSG_MASK
            #log.info('Got message: %s' % rx_msg)
            return rx_msg
        else:
            log.debug('read complete -> status not okay')
            

    def __write_process(self):
        while self.__threads_running:
            tx_msg = None
            have_lock = False
            try:
                if self.single_handle:
                    if not self.__tx_queue.empty():
                        # Tell the rx thread to give up the can handle
                        # because we have a message to write to the bus
                        self.writing_event.set()
                        # Acquire a lock that the rx thread has started waiting on
                        self.done_writing.acquire()
                        have_lock = True
                    else:
                        raise queue.Empty('')
                    
                while not self.__tx_queue.empty():
                    tx_msg = self.__tx_queue.get(timeout=0.05)
                    if tx_msg is not None:
                        self.__put_message(tx_msg)
                        
            except queue.Empty:
                pass
            if self.single_handle and have_lock:
                self.writing_event.clear()
                # Tell the rx thread it can start again
                self.done_writing.notify()
                self.done_writing.release()
                have_lock = False
            

    def __put_message(self, tx_msg):
        canWriteWait(self.__write_handle,
                            tx_msg.arbitration_id,
                            "".join([("%c" % byte) for byte in tx_msg.data]),
                             tx_msg.dlc,
                             tx_msg.flags,
                             5)

    def write_for_period(self, messageGapInSeconds, totalPeriodInSeconds, message):
        _startTime = time.time()
        while (time.time() - _startTime) < totalPeriodInSeconds:
            self.write(message)
            
            _startOfPause = time.time()
            while (time.time() - _startOfPause) < messageGapInSeconds and (time.time() - _startTime) < totalPeriodInSeconds:
                time.sleep(0.001)

    def write(self, msg):
        ''''
        @param msg A Message object to write to bus.
        '''
        self.__tx_queue.put_nowait(msg)

    def shutdown(self):
        self.__threads_running = False
        canBusOff(self.__write_handle)
        canClose(self.__write_handle)
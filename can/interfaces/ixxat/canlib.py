# -*- coding: utf-8 -*-
"""
Ctypes wrapper module for IXXAT Virtual CAN Interface V3 on win32 systems
Copyright (C) 2016 Giuseppe Corbelli <giuseppe.corbelli@weightpack.com>
"""

import binascii
import ctypes
import logging
import sys
import time

from can import CanError, BusABC
from can import Message
from can.interfaces.ixxat import constants, structures

from can.ctypesutil import CLibrary, HANDLE, PHANDLE

from .exceptions import *

__all__ = ["VCITimeout", "VCIError", "VCIDeviceNotFoundError", "IXXATBus"]

log = logging.getLogger('can.ixxat')

if (sys.version_info.major == 2):
    _timer_function = time.clock
elif (sys.version_info.major == 3):
    _timer_function = time.perf_counter

# main ctypes instance
if sys.platform == "win32":
    try:
        _canlib = CLibrary("vcinpl")
    except Exception as e:
        log.warning("Cannot load IXXAT vcinpl library: %s", e)
        _canlib = None
else:
    # Will not work on other systems, but have it importable anyway for
    # tests/sphinx
    log.warning("IXXAT VCI library does not work on %s platform", sys.platform)
    _canlib = None


def __check_status(result, function, arguments):
    if isinstance(result, int):
        # Real return value is an unsigned long
        result = ctypes.c_ulong(result).value

    if (result == constants.VCI_E_TIMEOUT):
        raise VCITimeout("Function {} timed out".format(function._name))
    elif (result == constants.VCI_E_NO_MORE_ITEMS):
        raise StopIteration()
    elif (result != constants.VCI_OK):
        raise VCIError(function, result, arguments)

    return result

try:
    # Map all required symbols and initialize library ---------------------------
    #HRESULT VCIAPI vciInitialize ( void );
    _canlib.map_symbol("vciInitialize", ctypes.c_long, (), __check_status)

    #void VCIAPI vciFormatError (HRESULT hrError, PCHAR pszText, UINT32 dwsize);
    _canlib.map_symbol("vciFormatError", None, (ctypes.HRESULT, ctypes.c_char_p, ctypes.c_uint32))

    # HRESULT VCIAPI vciEnumDeviceOpen( OUT PHANDLE hEnum );
    _canlib.map_symbol("vciEnumDeviceOpen", ctypes.c_long, (PHANDLE,), __check_status)
    # HRESULT VCIAPI vciEnumDeviceClose ( IN HANDLE hEnum );
    _canlib.map_symbol("vciEnumDeviceClose", ctypes.c_long, (HANDLE,), __check_status)
    # HRESULT VCIAPI vciEnumDeviceNext( IN  HANDLE hEnum, OUT PVCIDEVICEINFO pInfo );
    _canlib.map_symbol("vciEnumDeviceNext", ctypes.c_long, (HANDLE, structures.PVCIDEVICEINFO), __check_status)

    # HRESULT VCIAPI vciDeviceOpen( IN  REFVCIID rVciid, OUT PHANDLE  phDevice );
    _canlib.map_symbol("vciDeviceOpen", ctypes.c_long, (structures.PVCIID, PHANDLE), __check_status)
    # HRESULT vciDeviceClose( HANDLE hDevice )
    _canlib.map_symbol("vciDeviceClose", ctypes.c_long, (HANDLE,), __check_status)

    # HRESULT VCIAPI canChannelOpen( IN  HANDLE  hDevice, IN  UINT32  dwCanNo, IN  BOOL    fExclusive, OUT PHANDLE phCanChn );
    _canlib.map_symbol("canChannelOpen", ctypes.c_long, (HANDLE, ctypes.c_uint32, ctypes.c_long, PHANDLE), __check_status)
    # EXTERN_C HRESULT VCIAPI canChannelInitialize( IN HANDLE hCanChn, IN UINT16 wRxFifoSize, IN UINT16 wRxThreshold, IN UINT16 wTxFifoSize, IN UINT16 wTxThreshold );
    _canlib.map_symbol("canChannelInitialize", ctypes.c_long, (HANDLE, ctypes.c_uint16, ctypes.c_uint16, ctypes.c_uint16, ctypes.c_uint16), __check_status)
    # EXTERN_C HRESULT VCIAPI canChannelActivate( IN HANDLE hCanChn, IN BOOL   fEnable );
    _canlib.map_symbol("canChannelActivate", ctypes.c_long, (HANDLE, ctypes.c_long), __check_status)
    # HRESULT canChannelClose( HANDLE hChannel )
    _canlib.map_symbol("canChannelClose", ctypes.c_long, (HANDLE, ), __check_status)
    #EXTERN_C HRESULT VCIAPI canChannelReadMessage( IN  HANDLE  hCanChn, IN  UINT32  dwMsTimeout, OUT PCANMSG pCanMsg );
    _canlib.map_symbol("canChannelReadMessage", ctypes.c_long, (HANDLE, ctypes.c_uint32, structures.PCANMSG), __check_status)
    #HRESULT canChannelPeekMessage(HANDLE hChannel,PCANMSG pCanMsg );
    _canlib.map_symbol("canChannelPeekMessage", ctypes.c_long, (HANDLE, structures.PCANMSG), __check_status)
    #HRESULT canChannelWaitTxEvent (HANDLE hChannel UINT32 dwMsTimeout );
    _canlib.map_symbol("canChannelWaitTxEvent", ctypes.c_long, (HANDLE, ctypes.c_uint32), __check_status)
    #HRESULT canChannelWaitRxEvent (HANDLE hChannel, UINT32 dwMsTimeout );
    _canlib.map_symbol("canChannelWaitRxEvent", ctypes.c_long, (HANDLE, ctypes.c_uint32), __check_status)
    #HRESULT canChannelPostMessage (HANDLE hChannel, PCANMSG pCanMsg );
    _canlib.map_symbol("canChannelPostMessage", ctypes.c_long, (HANDLE, structures.PCANMSG), __check_status)

    #EXTERN_C HRESULT VCIAPI canControlOpen( IN  HANDLE  hDevice, IN  UINT32  dwCanNo, OUT PHANDLE phCanCtl );
    _canlib.map_symbol("canControlOpen", ctypes.c_long, (HANDLE, ctypes.c_uint32, PHANDLE), __check_status)
    #EXTERN_C HRESULT VCIAPI canControlInitialize( IN HANDLE hCanCtl, IN UINT8  bMode, IN UINT8  bBtr0, IN UINT8  bBtr1 );
    _canlib.map_symbol("canControlInitialize", ctypes.c_long, (HANDLE, ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8), __check_status)
    #EXTERN_C HRESULT VCIAPI canControlClose( IN HANDLE hCanCtl );
    _canlib.map_symbol("canControlClose", ctypes.c_long, (HANDLE,), __check_status)
    #EXTERN_C HRESULT VCIAPI canControlReset( IN HANDLE hCanCtl );
    _canlib.map_symbol("canControlReset", ctypes.c_long, (HANDLE,), __check_status)
    #EXTERN_C HRESULT VCIAPI canControlStart( IN HANDLE hCanCtl, IN BOOL   fStart );
    _canlib.map_symbol("canControlStart", ctypes.c_long, (HANDLE, ctypes.c_long), __check_status)
    #EXTERN_C HRESULT VCIAPI canControlGetStatus( IN  HANDLE         hCanCtl, OUT PCANLINESTATUS pStatus );
    _canlib.map_symbol("canControlGetStatus", ctypes.c_long, (HANDLE, structures.PCANLINESTATUS), __check_status)
    #EXTERN_C HRESULT VCIAPI canControlGetCaps( IN  HANDLE           hCanCtl, OUT PCANCAPABILITIES pCanCaps );
    _canlib.map_symbol("canControlGetCaps", ctypes.c_long, (HANDLE, structures.PCANCAPABILITIES), __check_status)
    #EXTERN_C HRESULT VCIAPI canControlSetAccFilter( IN HANDLE hCanCtl, IN BOOL   fExtend, IN UINT32 dwCode, IN UINT32 dwMask );
    _canlib.map_symbol("canControlSetAccFilter", ctypes.c_long, (HANDLE, ctypes.c_int, ctypes.c_uint32, ctypes.c_uint32), __check_status)
    #EXTERN_C HRESULT canControlAddFilterIds (HANDLE hControl, BOOL fExtended, UINT32 dwCode, UINT32 dwMask);
    _canlib.map_symbol("canControlAddFilterIds", ctypes.c_long, (HANDLE, ctypes.c_int, ctypes.c_uint32, ctypes.c_uint32), __check_status)
    #EXTERN_C HRESULT canControlRemFilterIds (HANDLE hControl, BOOL fExtendend, UINT32 dwCode, UINT32 dwMask );
    _canlib.map_symbol("canControlRemFilterIds", ctypes.c_long, (HANDLE, ctypes.c_int, ctypes.c_uint32, ctypes.c_uint32), __check_status)
    _canlib.vciInitialize()
except AttributeError:
    # In case _canlib == None meaning we're not on win32/no lib found
    pass
except Exception as e:
    log.warning("Could not initialize IXXAT VCI library: %s", e)
# ---------------------------------------------------------------------------


CAN_INFO_MESSAGES = {
    constants.CAN_INFO_START: "CAN started",
    constants.CAN_INFO_STOP: "CAN stopped",
    constants.CAN_INFO_RESET:"CAN resetted",
}

CAN_ERROR_MESSAGES = {
    constants.CAN_ERROR_STUFF: "CAN bit stuff error",
    constants.CAN_ERROR_FORM: "CAN form error",
    constants.CAN_ERROR_ACK: "CAN acknowledgment error",
    constants.CAN_ERROR_BIT: "CAN bit error",
    constants.CAN_ERROR_CRC: "CAN CRC error",
    constants.CAN_ERROR_OTHER: "Other (unknown) CAN error",
}
#----------------------------------------------------------------------------


class IXXATBus(BusABC):
    " The CAN Bus implemented for the IXXAT interface. "

    CHANNEL_BITRATES = {
        0: {
            10000: constants.CAN_BT0_10KB,
            20000: constants.CAN_BT0_20KB,
            50000: constants.CAN_BT0_50KB,
            100000: constants.CAN_BT0_100KB,
            125000: constants.CAN_BT0_125KB,
            250000: constants.CAN_BT0_250KB,
            500000: constants.CAN_BT0_500KB,
            800000: constants.CAN_BT0_800KB,
            1000000: constants.CAN_BT0_1000KB
        },
        1: {
            10000: constants.CAN_BT1_10KB,
            20000: constants.CAN_BT1_20KB,
            50000: constants.CAN_BT1_50KB,
            100000: constants.CAN_BT1_100KB,
            125000: constants.CAN_BT1_125KB,
            250000: constants.CAN_BT1_250KB,
            500000: constants.CAN_BT1_500KB,
            800000: constants.CAN_BT1_800KB,
            1000000: constants.CAN_BT1_1000KB
        }
    }

    def __init__(self, channel, can_filters=None, **config):
        """
        :param int channel:
            The Channel id to create this bus with.

        :param list can_filters:
            A list of dictionaries each containing a "can_id" and a "can_mask".

            >>> [{"can_id": 0x11, "can_mask": 0x21}]

        Backend Configuration
        ---------------------

        :param int UniqueHardwareId:
            UniqueHardwareId to connect (optional, will use the first found if not supplied)
        :param int bitrate
            Channel bitrate in bit/s
        """
        if (_canlib is None):
            raise ImportError("The IXXAT VCI library has not been initialized. Check the logs for more details.")
        log.info("CAN Filters: %s", can_filters)
        log.info("Got configuration of: %s", config)
        # Configuration options
        bitrate = config.get('bitrate', 500000)
        UniqueHardwareId = config.get('UniqueHardwareId', None)
        rxFifoSize = config.get('rxFifoSize', 16)
        txFifoSize = config.get('txFifoSize', 16)
        extended = config.get('extended', False)
        # Usually comes as a string from the config file
        channel = int(channel)

        if (bitrate not in self.CHANNEL_BITRATES[0]):
            raise ValueError("Invalid bitrate {}".format(bitrate))

        self._device_handle = HANDLE()
        self._device_info = structures.VCIDEVICEINFO()
        self._control_handle = HANDLE()
        self._channel_handle = HANDLE()
        self._channel_capabilities = structures.CANCAPABILITIES()
        self._message = structures.CANMSG()
        self._payload = (ctypes.c_byte * 8)()

        # Search for supplied device
        log.info("Searching for unique HW ID %s", UniqueHardwareId)
        _canlib.vciEnumDeviceOpen(ctypes.byref(self._device_handle))
        while True:
            try:
                _canlib.vciEnumDeviceNext(self._device_handle, ctypes.byref(self._device_info))
            except StopIteration:
                # TODO: better error message
                raise VCIDeviceNotFoundError("Unique HW ID {} not found".format(UniqueHardwareId))
            else:
                if (UniqueHardwareId is None) or (self._device_info.UniqueHardwareId.AsChar == bytes(UniqueHardwareId, 'ascii')):
                    break
        _canlib.vciEnumDeviceClose(self._device_handle)
        _canlib.vciDeviceOpen(ctypes.byref(self._device_info.VciObjectId), ctypes.byref(self._device_handle))
        log.info("Using unique HW ID %s", self._device_info.UniqueHardwareId.AsChar)

        log.info("Initializing channel %d in shared mode, %d rx buffers, %d tx buffers", channel, rxFifoSize, txFifoSize)
        _canlib.canChannelOpen(self._device_handle, channel, constants.FALSE, ctypes.byref(self._channel_handle))
        # Signal TX/RX events when at least one frame has been handled
        _canlib.canChannelInitialize(self._channel_handle, rxFifoSize, 1, txFifoSize, 1)
        _canlib.canChannelActivate(self._channel_handle, constants.TRUE)

        log.info("Initializing control %d bitrate %d", channel, bitrate)
        _canlib.canControlOpen(self._device_handle, channel, ctypes.byref(self._control_handle))
        _canlib.canControlInitialize(
            self._control_handle,
            constants.CAN_OPMODE_STANDARD|constants.CAN_OPMODE_EXTENDED|constants.CAN_OPMODE_ERRFRAME if extended else constants.CAN_OPMODE_STANDARD|constants.CAN_OPMODE_ERRFRAME,
            self.CHANNEL_BITRATES[0][bitrate],
            self.CHANNEL_BITRATES[1][bitrate]
        )
        _canlib.canControlGetCaps(self._control_handle, ctypes.byref(self._channel_capabilities))
        # With receive messages, this field contains the relative reception time of
        # the message in ticks. The resolution of a tick can be calculated from the fields
        # dwClockFreq and dwTscDivisor of the structure  CANCAPABILITIES in accor-
        # dance with the following formula:
        # Resolution [s] = dwTscDivisor / dwClockFreq
        # Reversed the terms, so that we have the number of ticks in a second
        self._tick_resolution =  self._channel_capabilities.dwClockFreq / self._channel_capabilities.dwTscDivisor

        # Setup filters before starting the channel
        if can_filters is not None and len(can_filters):
            log.info("The IXXAT VCI backend is filtering messages")
            # Disable every message coming in
            _canlib.canControlSetAccFilter(self._control_handle, 1 if extended else 0, constants.CAN_ACC_CODE_NONE, constants.CAN_ACC_MASK_NONE)
            for can_filter in can_filters:
                # Whitelist
                code = int(can_filter['can_id'])
                mask = int(can_filter['can_mask'])
                _canlib.canControlAddFilterIds(self._control_handle, 1 if extended else 0, code, mask)
                rtr = (code & 0x01) and (mask & 0x01)
                log.info("Accepting ID:%d  MASK:%d RTR:%s", code>>1, mask>>1, "YES" if rtr else "NO")

        # Start the CAN controller. Messages will be forwarded to the channel
        _canlib.canControlStart(self._control_handle, constants.TRUE)

        # Usually you get back 3 messages like "CAN initialized" ecc...
        # Filter them out with low timeout
        while (True):
            try:
                _canlib.canChannelWaitRxEvent(self._channel_handle, 0)
            except VCITimeout:
                break
            else:
                _canlib.canChannelReadMessage(self._channel_handle, 0, ctypes.byref(self._message))

        super(IXXATBus, self).__init__()

    def _inWaiting(self):
        try:
            _canlib.canChannelWaitRxEvent(self._channel_handle, 0)
        except VCITimeout:
            return 0
        else:
            return 1

    def flush_tx_buffer(self):
        " Flushes the transmit buffer on the IXXAT "
        # TODO: no timeout?
        _canlib.canChannelWaitTxEvent(self._channel_handle, constants.INFINITE)

    def recv(self, timeout=None):
        " Read a message from IXXAT device. "

        # TODO: handling CAN error messages?
        if (timeout is None):
            timeout = constants.INFINITE

        tm = None
        if (timeout == 0):
            # Peek without waiting
            try:
                _canlib.canChannelPeekMessage(self._channel_handle, ctypes.byref(self._message))
            except VCITimeout:
                return None
            except VCIError as e:
                if (e.HRESULT == constants.VCI_E_RXQUEUE_EMPTY):
                    return None
                else:
                    raise e
            else:
                if (self._message.uMsgInfo.Bits.type == constants.CAN_MSGTYPE_DATA):
                    tm = _timer_function()
        else:
            # Wait if no message available
            t0 = _timer_function()
            elapsed_ms = 0
            remaining_ms = 0
            while (elapsed_ms <= timeout):
                elapsed_ms = int((_timer_function() - t0) * 1000)
                remaining_ms = timeout - elapsed_ms
                # Wait until at least one frame is in the buffer
                try:
                    _canlib.canChannelWaitRxEvent(self._channel_handle, remaining_ms)
                except VCITimeout:
                    log.debug('canChannelWaitRxEvent timed out after %dms', remaining_ms)
                    return None

                # In theory we should be fine with a 0 timeout since the rxEvent was already
                # set but I've seen timeouts appearing here and there
                try:
                    _canlib.canChannelReadMessage(self._channel_handle, 0, ctypes.byref(self._message))
                except VCITimeout:
                    continue

                # See if we got a data or info/error messages
                if (self._message.uMsgInfo.Bits.type == constants.CAN_MSGTYPE_DATA):
                    tm = _timer_function()
                    break

                elif (self._message.uMsgInfo.Bits.type == constants.CAN_MSGTYPE_INFO):
                    log.info(CAN_INFO_MESSAGES.get(self._message.abData[0], "Unknown CAN info message code {}".format(self._message.abData[0])))

                elif (self._message.uMsgInfo.Bits.type == constants.CAN_MSGTYPE_ERROR):
                    log.warning(CAN_ERROR_MESSAGES.get(self._message.abData[0], "Unknown CAN error message code {}".format(self._message.abData[0])))

                elif (self._message.uMsgInfo.Bits.type == constants.CAN_MSGTYPE_TIMEOVR):
                    pass

        if (not tm):
            # Timed out / can message type is not DATA
            return None

        # The _message.dwTime is a 32bit tick value and will overrun,
        # so expect to see the value restarting from 0
        rx_msg = Message(
            self._message.dwTime / self._tick_resolution,  # Relative time in s
            True if self._message.uMsgInfo.Bits.rtr else False,
            True if self._message.uMsgInfo.Bits.ext else False,
            False,
            self._message.dwMsgId,
            self._message.uMsgInfo.Bits.dlc,
            self._message.abData
        )

        log.debug('Recv()ed message %s', rx_msg)
        return rx_msg

    def send(self, msg):
        log.debug("Sending message: %s", msg)

        # This system is not designed to be very efficient
        ctypes.memset(ctypes.byref(self._message), 0, ctypes.sizeof(structures.CANMSG))
        self._message.uMsgInfo.Bits.type = constants.CAN_MSGTYPE_DATA
        self._message.uMsgInfo.Bits.rtr = 1 if msg.is_remote_frame else 0
        self._message.uMsgInfo.Bits.ext = 1 if msg.id_type else 0
        self._message.dwMsgId = msg.arbitration_id
        if (msg.dlc):
            self._message.uMsgInfo.Bits.dlc = msg.dlc
            adapter = (ctypes.c_uint8 * msg.dlc).from_buffer(msg.data)
            ctypes.memmove(self._message.abData, adapter, msg.dlc)

        # This does not block but may raise if TX fifo is full
        # if you prefer a blocking call use canChannelSendMessage
        _canlib.canChannelPostMessage (self._channel_handle, self._message)

    def shutdown(self):
        _canlib.canChannelClose(self._channel_handle)
        _canlib.canControlStart(self._control_handle, constants.FALSE)
        _canlib.canControlClose(self._control_handle)
        _canlib.vciDeviceClose(self._device_handle)

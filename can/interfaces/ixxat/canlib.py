# -*- coding: utf-8 -*-

import binascii
import ctypes
import logging
import sys
import time

from can import CanError, BusABC
from can import Message
from can.interfaces.ixxat import constants, structures

__all__ = ["VCITimeout", "VCIError", "IXXATBus"]

log = logging.getLogger('can.ixxat')

# main ctypes instance
__canlib = None

try:
    if sys.platform == "win32":
        __canlib = ctypes.windll.LoadLibrary("vcinpl")
    else:
        raise ImportError("IXXAT VCI is only available on win32 systems. Use socketcan on Linux systems")
    log.info("loaded IXXAT CAN library")
except OSError as e:
    raise ImportError("IXXAT vcinpl.dll is unavailable: {}".format(e))


class VCITimeout(CanError):
    pass

class VCIError(CanError):
    " Try to display errors that occur within the wrapped C library nicely. "

    _ERROR_BUFFER = ctypes.create_string_buffer(constants.VCI_MAX_ERRSTRLEN)

    def __init__(self, function, HRESULT, arguments):
        super(VCIError, self).__init__()
        self.HRESULT = HRESULT
        self.function = function
        self.arguments = arguments

    def __str__(self):
        return "function {} failed - {} - arguments were {}".format(
            self.function.__name__,
            self.__get_error_message(),
            self.arguments
        )

    def __get_error_message(self):
        ctypes.memset(self._ERROR_BUFFER, 0, constants.VCI_MAX_ERRSTRLEN)
        vciFormatError(self.HRESULT, self._ERROR_BUFFER, constants.VCI_MAX_ERRSTRLEN)
        return "{}".format(self._ERROR_BUFFER)

class VCIDeviceNotFoundError(CanError):
    pass


def __get_canlib_function(func_name, argtypes=None, restype=None, errcheck=None):
    log.debug('Wrapping function "{}"'.format(func_name))
    try:
        retval = getattr(__canlib, func_name)
    except AttributeError:
        log.warning('Function {} was not found in library'.format(func_name))
    else:
        log.debug('Wrapped function "{}", result type: {}, error_check {}'.format(func_name, type(restype), errcheck))
        retval.argtypes = argtypes
        retval.restype = restype
        if (errcheck):
            retval.errcheck = errcheck
        return retval


def __check_status(result, function, arguments):
    if isinstance(result, int):
        # Real return value is an unsigned long
        result = ctypes.c_ulong(result).value

    if (result == constants.VCI_E_TIMEOUT):
        raise VCITimeout("Function {} timed out".format(function.__name__))
    if (result == constants.VCI_E_NO_MORE_ITEMS):
        raise StopIteration()
    elif (result != constants.VCI_OK):
        raise VCIError(function, result, arguments)

    return result

#HRESULT VCIAPI vciInitialize ( void );
vciInitialize = __get_canlib_function("vciInitialize", argtypes=[], restype=ctypes.c_long, errcheck=__check_status)

#void VCIAPI vciFormatError (HRESULT hrError, PCHAR pszText, UINT32 dwsize);
vciFormatError = __get_canlib_function("vciFormatError", argtypes=[ctypes.HRESULT, ctypes.c_char_p, ctypes.c_uint32], restype=None)

# HRESULT VCIAPI vciEnumDeviceOpen( OUT PHANDLE hEnum );
vciEnumDeviceOpen = __get_canlib_function("vciEnumDeviceOpen", argtypes=[structures.PHANDLE], restype=ctypes.c_long, errcheck=__check_status)
# HRESULT VCIAPI vciEnumDeviceClose ( IN HANDLE hEnum );
vciEnumDeviceClose = __get_canlib_function("vciEnumDeviceClose", argtypes=[structures.HANDLE], restype=ctypes.c_long, errcheck=__check_status)
# HRESULT VCIAPI vciEnumDeviceNext( IN  HANDLE hEnum, OUT PVCIDEVICEINFO pInfo );
vciEnumDeviceNext = __get_canlib_function("vciEnumDeviceNext", argtypes=[structures.HANDLE, structures.PVCIDEVICEINFO], restype=ctypes.c_long, errcheck=__check_status)

# HRESULT VCIAPI vciDeviceOpen( IN  REFVCIID rVciid, OUT PHANDLE  phDevice );
vciDeviceOpen = __get_canlib_function("vciDeviceOpen", argtypes=[structures.PVCIID, structures.PHANDLE], restype=ctypes.c_long, errcheck=__check_status)
# HRESULT vciDeviceClose( HANDLE hDevice )
vciDeviceClose = __get_canlib_function("vciDeviceClose", argtypes=[structures.HANDLE], restype=ctypes.c_long, errcheck=__check_status)

# HRESULT VCIAPI canChannelOpen( IN  HANDLE  hDevice, IN  UINT32  dwCanNo, IN  BOOL    fExclusive, OUT PHANDLE phCanChn );
canChannelOpen = __get_canlib_function("canChannelOpen", argtypes=[structures.HANDLE, ctypes.c_uint32, ctypes.c_long, structures.PHANDLE], restype=ctypes.c_long, errcheck=__check_status)
# EXTERN_C HRESULT VCIAPI canChannelInitialize( IN HANDLE hCanChn, IN UINT16 wRxFifoSize, IN UINT16 wRxThreshold, IN UINT16 wTxFifoSize, IN UINT16 wTxThreshold );
canChannelInitialize = __get_canlib_function("canChannelInitialize", argtypes=[structures.HANDLE, ctypes.c_uint16, ctypes.c_uint16, ctypes.c_uint16, ctypes.c_uint16], restype=ctypes.c_long, errcheck=__check_status)
# EXTERN_C HRESULT VCIAPI canChannelActivate( IN HANDLE hCanChn, IN BOOL   fEnable );
canChannelActivate = __get_canlib_function("canChannelActivate", argtypes=[structures.HANDLE, ctypes.c_long], restype=ctypes.c_long, errcheck=__check_status)
# HRESULT canChannelClose( HANDLE hChannel )
canChannelClose = __get_canlib_function("canChannelClose", argtypes=[structures.HANDLE], restype=ctypes.c_long, errcheck=__check_status)
#EXTERN_C HRESULT VCIAPI canChannelReadMessage( IN  HANDLE  hCanChn, IN  UINT32  dwMsTimeout, OUT PCANMSG pCanMsg );
canChannelReadMessage = __get_canlib_function("canChannelReadMessage", argtypes=[structures.HANDLE, ctypes.c_uint32, structures.PCANMSG], restype=ctypes.c_long, errcheck=__check_status)
#HRESULT canChannelPeekMessage(HANDLE hChannel,PCANMSG pCanMsg );
canChannelPeekMessage = __get_canlib_function("canChannelPeekMessage", argtypes=[structures.HANDLE, structures.PCANMSG], restype=ctypes.c_long, errcheck=__check_status)
#HRESULT canChannelWaitTxEvent (HANDLE hChannel UINT32 dwMsTimeout );
canChannelWaitTxEvent = __get_canlib_function("canChannelWaitTxEvent", argtypes=[structures.HANDLE, ctypes.c_uint32], restype=ctypes.c_long, errcheck=__check_status)
#HRESULT canChannelPostMessage (HANDLE hChannel, PCANMSG pCanMsg );
canChannelPostMessage = __get_canlib_function("canChannelPostMessage", argtypes=[structures.HANDLE, structures.PCANMSG], restype=ctypes.c_long, errcheck=__check_status)

#EXTERN_C HRESULT VCIAPI canControlOpen( IN  HANDLE  hDevice, IN  UINT32  dwCanNo, OUT PHANDLE phCanCtl );
canControlOpen = __get_canlib_function("canControlOpen", argtypes=[structures.HANDLE, ctypes.c_uint32, structures.PHANDLE], restype=ctypes.c_long, errcheck=__check_status)
#EXTERN_C HRESULT VCIAPI canControlInitialize( IN HANDLE hCanCtl, IN UINT8  bMode, IN UINT8  bBtr0, IN UINT8  bBtr1 );
canControlInitialize = __get_canlib_function("canControlInitialize", argtypes=[structures.HANDLE, ctypes.c_uint8, ctypes.c_uint8, ctypes.c_uint8], restype=ctypes.c_long, errcheck=__check_status)
#EXTERN_C HRESULT VCIAPI canControlClose( IN HANDLE hCanCtl );
canControlClose = __get_canlib_function("canControlClose", argtypes=[structures.HANDLE], restype=ctypes.c_long, errcheck=__check_status)
#EXTERN_C HRESULT VCIAPI canControlReset( IN HANDLE hCanCtl );
canControlReset = __get_canlib_function("canControlReset", argtypes=[structures.HANDLE], restype=ctypes.c_long, errcheck=__check_status)
#EXTERN_C HRESULT VCIAPI canControlStart( IN HANDLE hCanCtl, IN BOOL   fStart );
canControlStart = __get_canlib_function("canControlStart", argtypes=[structures.HANDLE, ctypes.c_long], restype=ctypes.c_long, errcheck=__check_status)
#EXTERN_C HRESULT VCIAPI canControlGetStatus( IN  HANDLE         hCanCtl, OUT PCANLINESTATUS pStatus );
canControlGetStatus = __get_canlib_function("canControlGetStatus", argtypes=[structures.HANDLE, structures.PCANLINESTATUS], restype=ctypes.c_long, errcheck=__check_status)
#EXTERN_C HRESULT VCIAPI canControlGetCaps( IN  HANDLE           hCanCtl, OUT PCANCAPABILITIES pCanCaps );
canControlGetCaps = __get_canlib_function("canControlGetCaps", argtypes=[structures.HANDLE, structures.PCANCAPABILITIES], restype=ctypes.c_long, errcheck=__check_status)


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
        log.info("CAN Filters: {}".format(can_filters))
        log.info("Got configuration of: {}".format(config))
        # Configuration options
        bitrate = config.get('bitrate', 500000)
        UniqueHardwareId = config.get('UniqueHardwareId', None)
        rxFifoSize = config.get('rxFifoSize', 16)
        txFifoSize = config.get('txFifoSize', 16)
        extended = config.get('extended', False)
        # Usually comes as a string from the config file
        channel = int(channel)

        if (bitrate not in self.CHANNEL_BITRATES[0]):
            raise VCIError("Invalid bitrate {}".format(bitrate))

        self._device_handle = structures.HANDLE()
        self._device_info = structures.VCIDEVICEINFO()
        self._control_handle = structures.HANDLE()
        self._channel_handle = structures.HANDLE()
        self._channel_capabilities = structures.CANCAPABILITIES()
        self._message = structures.CANMSG()
        self._payload = (ctypes.c_byte * 8)()

        # Search for supplied device
        log.info("Searching for unique HW ID {}".format(UniqueHardwareId))
        vciEnumDeviceOpen(ctypes.byref(self._device_handle))
        while True:
            try:
                vciEnumDeviceNext(self._device_handle, ctypes.byref(self._device_info))
            except StopIteration:
                # TODO: better error message
                raise VCIDeviceNotFoundError("Unique HW ID {} not found".format(UniqueHardwareId))
            else:
                if (UniqueHardwareId is None) or (self._device_info.UniqueHardwareId.AsChar == bytes(UniqueHardwareId, 'ascii')):
                    break
        vciEnumDeviceClose(self._device_handle)
        vciDeviceOpen(ctypes.byref(self._device_info.VciObjectId), ctypes.byref(self._device_handle))
        log.info("Using unique HW ID {}".format(self._device_info.UniqueHardwareId.AsChar))

        log.info("Initializing channel {} in shared mode, {} rx buffers, {} tx buffers".format(channel, rxFifoSize, txFifoSize))
        canChannelOpen(self._device_handle, channel, constants.FALSE, ctypes.byref(self._channel_handle))
        canChannelInitialize(self._channel_handle, rxFifoSize, rxFifoSize, txFifoSize, txFifoSize)
        canChannelActivate(self._channel_handle, constants.TRUE)

        log.info("Initializing control {} bitrate {}".format(channel, bitrate))
        canControlOpen(self._device_handle, channel, ctypes.byref(self._control_handle))
        canControlInitialize(
            self._control_handle,
            constants.CAN_OPMODE_STANDARD|constants.CAN_OPMODE_EXTENDED|constants.CAN_OPMODE_ERRFRAME if extended else constants.CAN_OPMODE_STANDARD|constants.CAN_OPMODE_ERRFRAME,
            self.CHANNEL_BITRATES[0][bitrate],
            self.CHANNEL_BITRATES[1][bitrate]
        )
        canControlGetCaps(self._control_handle, ctypes.byref(self._channel_capabilities))
        # Start the CAN controller. Messages will be forwarded to the channel
        canControlStart(self._control_handle, constants.TRUE)

        # TODO: filter messages

        #~ if can_filters is not None and len(can_filters):
            #~ log.warning("The ixxat VCI backend is filtering messages")
            #~ code, mask = 0, 0
            #~ for can_filter in can_filters:
                #~ code |= can_filter['can_id']
                #~ mask |= can_filter['can_mask']
            #~ log.warning("Filtering on: {}  {}".format(code, mask))

        super(IXXATBus, self).__init__()

    def flush_tx_buffer(self):
        " Flushes the transmit buffer on the IXXAT "
        # TODO: no timeout?
        canChannelWaitTxEvent(self._channel_handle, constants.INFINITE)

    def recv(self, timeout=None):
        " Read a message from IXXAT device. "

        # TODO: is the timestamp management enough?
        # TODO: handling CAN error messages?
        if (timeout is None):
            timeout = constants.INFINITE

        log.debug('Recv()ing message with timeout {}'.format(timeout))
        tm = None
        if (not timeout):
            try:
                canChannelPeekMessage(self._channel_handle, ctypes.byref(self._message))
            except VCITimeout:
                return None
            except VCIError as e:
                if (e.HRESULT == constants.VCI_E_RXQUEUE_EMPTY):
                    return None
                else:
                    raise e
            else:
                if (self._message.uMsgInfo.Bits.type == constants.CAN_MSGTYPE_DATA):
                    tm = time.perf_counter()
        else:
            t0 = time.perf_counter()
            t1 = t0 + (float(timeout)/1000)
            while (time.perf_counter() <= t1):
                try:
                    canChannelReadMessage(self._channel_handle, timeout, ctypes.byref(self._message))
                except VCITimeout:
                    return None

                # See if we got a data or info/error messages
                if (self._message.uMsgInfo.Bits.type == constants.CAN_MSGTYPE_DATA):
                    tm = time.perf_counter()
                    break

        if (not tm):
            # Timed out / can message type is not DATA
            return None

        rx_msg = Message(
            tm,
            True if self._message.uMsgInfo.Bits.rtr else False,
            True if self._message.uMsgInfo.Bits.ext else False,
            False,
            self._message.dwMsgId,
            self._message.uMsgInfo.Bits.dlc,
            self._message.abData
        )

        log.debug('Recv()ed message  {}'.format(rx_msg))
        return rx_msg

    def send(self, msg):
        log.debug("Sending message: {}".format(msg))

        # This system is not designed to be very efficient
        ctypes.memset(self._message, 0, ctypes.sizeof(structures.CANMSG))
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
        canChannelPostMessage (self._channel_handle, self._message)

    def shutdown(self):
        canChannelClose(self._channel_handle)
        canControlStart(self._control_handle, constants.FALSE)
        canControlClose(self._control_handle)
        vciDeviceClose(self._device_handle)


vciInitialize()

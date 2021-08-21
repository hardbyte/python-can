"""
Ctypes wrapper module for IXXAT Virtual CAN Interface V3 on win32 systems

TODO: We could implement this interface such that setting other filters
      could work when the initial filters were set to zero using the
      software fallback. Or could the software filters even be changed
      after the connection was opened? We need to document that bahaviour!
      See also the NICAN interface.

"""

import ctypes
import functools
import logging
import sys
from typing import Optional

from can import BusABC, Message
from can.exceptions import CanInterfaceNotImplementedError, CanInitializationError
from can.broadcastmanager import (
    LimitedDurationCyclicSendTaskABC,
    RestartableCyclicTaskABC,
)
from can.ctypesutil import CLibrary, HANDLE, PHANDLE, HRESULT as ctypes_HRESULT

import can.util

from . import constants, structures
from .exceptions import *

__all__ = [
    "VCITimeout",
    "VCIError",
    "VCIBusOffError",
    "VCIDeviceNotFoundError",
    "IXXATBus",
    "vciFormatError",
]

log = logging.getLogger("can.ixxat_fd")

from time import perf_counter as _timer_function

# Hack to have vciFormatError as a free function, see below
vciFormatError = None

# main ctypes instance
_canlib = None
# TODO: Use ECI driver for linux
if sys.platform == "win32" or sys.platform == "cygwin":
    try:
        _canlib = CLibrary("vcinpl2.dll")
    except Exception as e:
        log.warning("Cannot load IXXAT vcinpl library: %s", e)
else:
    # Will not work on other systems, but have it importable anyway for
    # tests/sphinx
    log.warning("IXXAT VCI library does not work on %s platform", sys.platform)


def __vciFormatErrorExtended(library_instance, function, HRESULT, arguments):
    """Format a VCI error and attach failed function, decoded HRESULT and arguments
    :param CLibrary library_instance:
        Mapped instance of IXXAT vcinpl library
    :param callable function:
        Failed function
    :param HRESULT HRESULT:
        HRESULT returned by vcinpl call
    :param arguments:
        Arbitrary arguments tuple
    :return:
        Formatted string
    """
    # TODO: make sure we don't generate another exception
    return "{} - arguments were {}".format(
        __vciFormatError(library_instance, function, HRESULT), arguments
    )


def __vciFormatError(library_instance, function, HRESULT):
    """Format a VCI error and attach failed function and decoded HRESULT
    :param CLibrary library_instance:
        Mapped instance of IXXAT vcinpl library
    :param callable function:
        Failed function
    :param HRESULT HRESULT:
        HRESULT returned by vcinpl call
    :return:
        Formatted string
    """
    buf = ctypes.create_string_buffer(constants.VCI_MAX_ERRSTRLEN)
    ctypes.memset(buf, 0, constants.VCI_MAX_ERRSTRLEN)
    library_instance.vciFormatError(HRESULT, buf, constants.VCI_MAX_ERRSTRLEN)
    return "function {} failed ({})".format(
        function._name, buf.value.decode("utf-8", "replace")
    )


def __check_status(result, function, arguments):
    """
    Check the result of a vcinpl function call and raise appropriate exception
    in case of an error. Used as errcheck function when mapping C functions
    with ctypes.
        :param result:
            Function call numeric result
        :param callable function:
            Called function
        :param arguments:
            Arbitrary arguments tuple
        :raise:
            :class:VCITimeout
            :class:VCIRxQueueEmptyError
            :class:StopIteration
            :class:VCIError
    """
    if isinstance(result, int):
        # Real return value is an unsigned long
        result = ctypes.c_ulong(result).value

    if result == constants.VCI_E_TIMEOUT:
        raise VCITimeout("Function {} timed out".format(function._name))
    elif result == constants.VCI_E_RXQUEUE_EMPTY:
        raise VCIRxQueueEmptyError()
    elif result == constants.VCI_E_NO_MORE_ITEMS:
        raise StopIteration()
    elif result == constants.VCI_E_ACCESSDENIED:
        pass  # not a real error, might happen if another program has initialized the bus
    elif result != constants.VCI_OK:
        raise VCIError(vciFormatError(function, result))

    return result


try:
    # Map all required symbols and initialize library ---------------------------
    # HRESULT VCIAPI vciInitialize ( void );
    _canlib.map_symbol("vciInitialize", ctypes.c_long, (), __check_status)

    # void VCIAPI vciFormatError (HRESULT hrError, PCHAR pszText, UINT32 dwsize);
    try:
        _canlib.map_symbol(
            "vciFormatError", None, (ctypes_HRESULT, ctypes.c_char_p, ctypes.c_uint32)
        )
    except:
        _canlib.map_symbol(
            "vciFormatErrorA", None, (ctypes_HRESULT, ctypes.c_char_p, ctypes.c_uint32)
        )
        _canlib.vciFormatError = _canlib.vciFormatErrorA
    # Hack to have vciFormatError as a free function
    vciFormatError = functools.partial(__vciFormatError, _canlib)

    # HRESULT VCIAPI vciEnumDeviceOpen( OUT PHANDLE hEnum );
    _canlib.map_symbol("vciEnumDeviceOpen", ctypes.c_long, (PHANDLE,), __check_status)
    # HRESULT VCIAPI vciEnumDeviceClose ( IN HANDLE hEnum );
    _canlib.map_symbol("vciEnumDeviceClose", ctypes.c_long, (HANDLE,), __check_status)
    # HRESULT VCIAPI vciEnumDeviceNext( IN  HANDLE hEnum, OUT PVCIDEVICEINFO pInfo );
    _canlib.map_symbol(
        "vciEnumDeviceNext",
        ctypes.c_long,
        (HANDLE, structures.PVCIDEVICEINFO),
        __check_status,
    )

    # HRESULT VCIAPI vciDeviceOpen( IN  REFVCIID rVciid, OUT PHANDLE  phDevice );
    _canlib.map_symbol(
        "vciDeviceOpen", ctypes.c_long, (structures.PVCIID, PHANDLE), __check_status
    )
    # HRESULT vciDeviceClose( HANDLE hDevice )
    _canlib.map_symbol("vciDeviceClose", ctypes.c_long, (HANDLE,), __check_status)

    # HRESULT VCIAPI canChannelOpen( IN  HANDLE  hDevice, IN  UINT32  dwCanNo, IN  BOOL    fExclusive, OUT PHANDLE phCanChn );
    _canlib.map_symbol(
        "canChannelOpen",
        ctypes.c_long,
        (HANDLE, ctypes.c_uint32, ctypes.c_long, PHANDLE),
        __check_status,
    )
    # EXTERN_C HRESULT VCIAPI canChannelInitialize( IN HANDLE hCanChn, IN UINT16 wRxFifoSize, IN UINT16 wRxThreshold, IN UINT16 wTxFifoSize, IN UINT16 wTxThreshold );
    _canlib.map_symbol(
        "canChannelInitialize",
        ctypes.c_long,
        (
            HANDLE,
            ctypes.c_uint16,
            ctypes.c_uint16,
            ctypes.c_uint16,
            ctypes.c_uint16,
            ctypes.c_uint32,
            ctypes.c_uint8,
        ),
        __check_status,
    )
    # EXTERN_C HRESULT VCIAPI canChannelActivate( IN HANDLE hCanChn, IN BOOL   fEnable );
    _canlib.map_symbol(
        "canChannelActivate", ctypes.c_long, (HANDLE, ctypes.c_long), __check_status
    )
    # HRESULT canChannelClose( HANDLE hChannel )
    _canlib.map_symbol("canChannelClose", ctypes.c_long, (HANDLE,), __check_status)
    # EXTERN_C HRESULT VCIAPI canChannelReadMessage( IN  HANDLE  hCanChn, IN  UINT32  dwMsTimeout, OUT PCANMSG pCanMsg );
    _canlib.map_symbol(
        "canChannelReadMessage",
        ctypes.c_long,
        (HANDLE, ctypes.c_uint32, structures.PCANMSG2),
        __check_status,
    )
    # HRESULT canChannelPeekMessage(HANDLE hChannel,PCANMSG pCanMsg );
    _canlib.map_symbol(
        "canChannelPeekMessage",
        ctypes.c_long,
        (HANDLE, structures.PCANMSG2),
        __check_status,
    )
    # HRESULT canChannelWaitTxEvent (HANDLE hChannel UINT32 dwMsTimeout );
    _canlib.map_symbol(
        "canChannelWaitTxEvent",
        ctypes.c_long,
        (HANDLE, ctypes.c_uint32),
        __check_status,
    )
    # HRESULT canChannelWaitRxEvent (HANDLE hChannel, UINT32 dwMsTimeout );
    _canlib.map_symbol(
        "canChannelWaitRxEvent",
        ctypes.c_long,
        (HANDLE, ctypes.c_uint32),
        __check_status,
    )
    # HRESULT canChannelPostMessage (HANDLE hChannel, PCANMSG pCanMsg );
    _canlib.map_symbol(
        "canChannelPostMessage",
        ctypes.c_long,
        (HANDLE, structures.PCANMSG2),
        __check_status,
    )
    # HRESULT canChannelSendMessage (HANDLE hChannel, UINT32 dwMsTimeout, PCANMSG pCanMsg );
    _canlib.map_symbol(
        "canChannelSendMessage",
        ctypes.c_long,
        (HANDLE, ctypes.c_uint32, structures.PCANMSG2),
        __check_status,
    )

    # EXTERN_C HRESULT VCIAPI canControlOpen( IN  HANDLE  hDevice, IN  UINT32  dwCanNo, OUT PHANDLE phCanCtl );
    _canlib.map_symbol(
        "canControlOpen",
        ctypes.c_long,
        (HANDLE, ctypes.c_uint32, PHANDLE),
        __check_status,
    )
    # EXTERN_C HRESULT VCIAPI canControlInitialize( IN HANDLE hCanCtl, IN UINT8  bMode, IN UINT8  bBtr0, IN UINT8  bBtr1 );
    _canlib.map_symbol(
        "canControlInitialize",
        ctypes.c_long,
        (
            HANDLE,
            ctypes.c_uint8,
            ctypes.c_uint8,
            ctypes.c_uint8,
            ctypes.c_uint8,
            ctypes.c_uint32,
            ctypes.c_uint32,
            structures.PCANBTP,
            structures.PCANBTP,
        ),
        __check_status,
    )
    # EXTERN_C HRESULT VCIAPI canControlClose( IN HANDLE hCanCtl );
    _canlib.map_symbol("canControlClose", ctypes.c_long, (HANDLE,), __check_status)
    # EXTERN_C HRESULT VCIAPI canControlReset( IN HANDLE hCanCtl );
    _canlib.map_symbol("canControlReset", ctypes.c_long, (HANDLE,), __check_status)
    # EXTERN_C HRESULT VCIAPI canControlStart( IN HANDLE hCanCtl, IN BOOL   fStart );
    _canlib.map_symbol(
        "canControlStart", ctypes.c_long, (HANDLE, ctypes.c_long), __check_status
    )
    # EXTERN_C HRESULT VCIAPI canControlGetStatus( IN  HANDLE         hCanCtl, OUT PCANLINESTATUS pStatus );
    _canlib.map_symbol(
        "canControlGetStatus",
        ctypes.c_long,
        (HANDLE, structures.PCANLINESTATUS2),
        __check_status,
    )
    # EXTERN_C HRESULT VCIAPI canControlGetCaps( IN  HANDLE           hCanCtl, OUT PCANCAPABILITIES pCanCaps );
    _canlib.map_symbol(
        "canControlGetCaps",
        ctypes.c_long,
        (HANDLE, structures.PCANCAPABILITIES2),
        __check_status,
    )
    # EXTERN_C HRESULT VCIAPI canControlSetAccFilter( IN HANDLE hCanCtl, IN BOOL   fExtend, IN UINT32 dwCode, IN UINT32 dwMask );
    _canlib.map_symbol(
        "canControlSetAccFilter",
        ctypes.c_long,
        (HANDLE, ctypes.c_int, ctypes.c_uint32, ctypes.c_uint32),
        __check_status,
    )
    # EXTERN_C HRESULT canControlAddFilterIds (HANDLE hControl, BOOL fExtended, UINT32 dwCode, UINT32 dwMask);
    _canlib.map_symbol(
        "canControlAddFilterIds",
        ctypes.c_long,
        (HANDLE, ctypes.c_int, ctypes.c_uint32, ctypes.c_uint32),
        __check_status,
    )
    # EXTERN_C HRESULT canControlRemFilterIds (HANDLE hControl, BOOL fExtendend, UINT32 dwCode, UINT32 dwMask );
    _canlib.map_symbol(
        "canControlRemFilterIds",
        ctypes.c_long,
        (HANDLE, ctypes.c_int, ctypes.c_uint32, ctypes.c_uint32),
        __check_status,
    )
    # EXTERN_C HRESULT canSchedulerOpen (HANDLE hDevice, UINT32 dwCanNo, PHANDLE phScheduler );
    _canlib.map_symbol(
        "canSchedulerOpen",
        ctypes.c_long,
        (HANDLE, ctypes.c_uint32, PHANDLE),
        __check_status,
    )
    # EXTERN_C HRESULT canSchedulerClose (HANDLE hScheduler );
    _canlib.map_symbol("canSchedulerClose", ctypes.c_long, (HANDLE,), __check_status)
    # EXTERN_C HRESULT canSchedulerGetCaps (HANDLE hScheduler, PCANCAPABILITIES pCaps );
    _canlib.map_symbol(
        "canSchedulerGetCaps",
        ctypes.c_long,
        (HANDLE, structures.PCANCAPABILITIES2),
        __check_status,
    )
    # EXTERN_C HRESULT canSchedulerActivate ( HANDLE hScheduler, BOOL fEnable );
    _canlib.map_symbol(
        "canSchedulerActivate", ctypes.c_long, (HANDLE, ctypes.c_int), __check_status
    )
    # EXTERN_C HRESULT canSchedulerAddMessage (HANDLE hScheduler, PCANCYCLICTXMSG pMessage, PUINT32 pdwIndex );
    _canlib.map_symbol(
        "canSchedulerAddMessage",
        ctypes.c_long,
        (HANDLE, structures.PCANCYCLICTXMSG2, ctypes.POINTER(ctypes.c_uint32)),
        __check_status,
    )
    # EXTERN_C HRESULT canSchedulerRemMessage (HANDLE hScheduler, UINT32 dwIndex );
    _canlib.map_symbol(
        "canSchedulerRemMessage",
        ctypes.c_long,
        (HANDLE, ctypes.c_uint32),
        __check_status,
    )
    # EXTERN_C HRESULT canSchedulerStartMessage (HANDLE hScheduler, UINT32 dwIndex, UINT16 dwCount );
    _canlib.map_symbol(
        "canSchedulerStartMessage",
        ctypes.c_long,
        (HANDLE, ctypes.c_uint32, ctypes.c_uint16),
        __check_status,
    )
    # EXTERN_C HRESULT canSchedulerStopMessage (HANDLE hScheduler, UINT32 dwIndex );
    _canlib.map_symbol(
        "canSchedulerStopMessage",
        ctypes.c_long,
        (HANDLE, ctypes.c_uint32),
        __check_status,
    )
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
    constants.CAN_INFO_RESET: "CAN reset",
}

CAN_ERROR_MESSAGES = {
    constants.CAN_ERROR_STUFF: "CAN bit stuff error",
    constants.CAN_ERROR_FORM: "CAN form error",
    constants.CAN_ERROR_ACK: "CAN acknowledgment error",
    constants.CAN_ERROR_BIT: "CAN bit error",
    constants.CAN_ERROR_CRC: "CAN CRC error",
    constants.CAN_ERROR_OTHER: "Other (unknown) CAN error",
}

CAN_STATUS_FLAGS = {
    constants.CAN_STATUS_TXPEND: "transmission pending",
    constants.CAN_STATUS_OVRRUN: "data overrun occurred",
    constants.CAN_STATUS_ERRLIM: "error warning limit exceeded",
    constants.CAN_STATUS_BUSOFF: "bus off",
    constants.CAN_STATUS_ININIT: "init mode active",
    constants.CAN_STATUS_BUSCERR: "bus coupling error",
}
# ----------------------------------------------------------------------------


class IXXATBus(BusABC):
    """The CAN Bus implemented for the IXXAT interface.

    .. warning::

        This interface does implement efficient filtering of messages, but
        the filters have to be set in :meth:`~can.interfaces.ixxat.IXXATBus.__init__`
        using the ``can_filters`` parameter. Using :meth:`~can.interfaces.ixxat.IXXATBus.set_filters`
        does not work.

    """

    def __init__(self, channel, can_filters=None, **kwargs):
        """
        :param int channel:
            The Channel id to create this bus with.

        :param list can_filters:
            See :meth:`can.BusABC.set_filters`.

        :param bool receive_own_messages:
            Enable self-reception of sent messages.

        :param int UniqueHardwareId:
            UniqueHardwareId to connect (optional, will use the first found if not supplied)

        :param int bitrate:
            Channel bitrate in bit/s
        """
        if _canlib is None:
            raise CanInterfaceNotImplementedError(
                "The IXXAT VCI library has not been initialized. Check the logs for more details."
            )
        log.info("CAN Filters: %s", can_filters)
        log.info("Got configuration of: %s", kwargs)
        # Configuration options
        bitrate = kwargs.get("bitrate", 500000)
        data_bitrate = kwargs.get("data_bitrate", 2000000)
        UniqueHardwareId = kwargs.get("UniqueHardwareId", None)
        rxFifoSize = kwargs.get("rxFifoSize", 1024)
        txFifoSize = kwargs.get("txFifoSize", 128)
        extended = kwargs.get("extended", False)
        self._receive_own_messages = kwargs.get("receive_own_messages", False)
        # Usually comes as a string from the config file
        channel = int(channel)

        if bitrate not in constants.CAN_BITRATE_PRESETS:
            raise ValueError("Invalid bitrate {}".format(bitrate))

        if data_bitrate not in constants.CAN_DATABITRATE_PRESETS:
            raise ValueError("Invalid bitrate {}".format(bitrate))

        if rxFifoSize <= 0:
            raise ValueError("rxFifoSize must be > 0")

        if txFifoSize <= 0:
            raise ValueError("txFifoSize must be > 0")

        if channel < 0:
            raise ValueError("channel number must be >= 0")

        self._device_handle = HANDLE()
        self._device_info = structures.VCIDEVICEINFO()
        self._control_handle = HANDLE()
        self._channel_handle = HANDLE()
        self._channel_capabilities = structures.CANCAPABILITIES2()
        self._message = structures.CANMSG2()
        self._payload = (ctypes.c_byte * 64)()

        # Search for supplied device
        if UniqueHardwareId is None:
            log.info("Searching for first available device")
        else:
            log.info("Searching for unique HW ID %s", UniqueHardwareId)
        _canlib.vciEnumDeviceOpen(ctypes.byref(self._device_handle))
        while True:
            try:
                _canlib.vciEnumDeviceNext(
                    self._device_handle, ctypes.byref(self._device_info)
                )
            except StopIteration:
                if UniqueHardwareId is None:
                    raise VCIDeviceNotFoundError(
                        "No IXXAT device(s) connected or device(s) in use by other process(es)."
                    )
                else:
                    raise VCIDeviceNotFoundError(
                        "Unique HW ID {} not connected or not available.".format(
                            UniqueHardwareId
                        )
                    )
            else:
                if (UniqueHardwareId is None) or (
                    self._device_info.UniqueHardwareId.AsChar
                    == bytes(UniqueHardwareId, "ascii")
                ):
                    break
                else:
                    log.debug(
                        "Ignoring IXXAT with hardware id '%s'.",
                        self._device_info.UniqueHardwareId.AsChar.decode("ascii"),
                    )
        _canlib.vciEnumDeviceClose(self._device_handle)

        try:
            _canlib.vciDeviceOpen(
                ctypes.byref(self._device_info.VciObjectId),
                ctypes.byref(self._device_handle),
            )
        except Exception as exception:
            raise CanInitializationError(f"Could not open device: {exception}")

        log.info("Using unique HW ID %s", self._device_info.UniqueHardwareId.AsChar)

        log.info(
            "Initializing channel %d in shared mode, %d rx buffers, %d tx buffers",
            channel,
            rxFifoSize,
            txFifoSize,
        )

        try:
            _canlib.canChannelOpen(
                self._device_handle,
                channel,
                constants.FALSE,
                ctypes.byref(self._channel_handle),
            )
        except Exception as exception:
            raise CanInitializationError(
                f"Could not open and initialize channel: {exception}"
            )

        # Signal TX/RX events when at least one frame has been handled
        _canlib.canChannelInitialize(
            self._channel_handle,
            rxFifoSize,
            1,
            txFifoSize,
            1,
            0,
            constants.CAN_FILTER_PASS,
        )
        _canlib.canChannelActivate(self._channel_handle, constants.TRUE)

        pBtpSDR = constants.CAN_BITRATE_PRESETS[bitrate]
        pBtpFDR = constants.CAN_DATABITRATE_PRESETS[data_bitrate]
        log.info(
            "Initializing control %d with SDR={%s}, FDR={%s}",
            channel,
            pBtpSDR,
            pBtpFDR,
        )
        _canlib.canControlOpen(
            self._device_handle, channel, ctypes.byref(self._control_handle)
        )

        _canlib.canControlGetCaps(
            self._control_handle, ctypes.byref(self._channel_capabilities)
        )

        # check capabilities
        bOpMode = constants.CAN_OPMODE_UNDEFINED
        if (
            self._channel_capabilities.dwFeatures & constants.CAN_FEATURE_STDANDEXT
        ) != 0:
            # controller supportes CAN_OPMODE_STANDARD and CAN_OPMODE_EXTENDED at the same time
            bOpMode |= constants.CAN_OPMODE_STANDARD  # enable both 11 bits reception
            if extended:  # parameter from configuration
                bOpMode |= constants.CAN_OPMODE_EXTENDED  # enable 29 bits reception
        elif (
            self._channel_capabilities.dwFeatures & constants.CAN_FEATURE_STDANDEXT
        ) != 0:
            log.warning(
                "Channel %d capabilities allow either basic or extended IDs, but not both. using %s according to parameter [extended=%s]",
                channel,
                "extended" if extended else "basic",
                "True" if extended else "False",
            )
            bOpMode |= (
                constants.CAN_OPMODE_EXTENDED
                if extended
                else constants.CAN_OPMODE_STANDARD
            )

        if (
            self._channel_capabilities.dwFeatures & constants.CAN_FEATURE_ERRFRAME
        ) != 0:
            bOpMode |= constants.CAN_OPMODE_ERRFRAME

        bExMode = constants.CAN_EXMODE_DISABLED
        if (self._channel_capabilities.dwFeatures & constants.CAN_FEATURE_EXTDATA) != 0:
            bExMode |= constants.CAN_EXMODE_EXTDATALEN

        if (
            self._channel_capabilities.dwFeatures & constants.CAN_FEATURE_FASTDATA
        ) != 0:
            bExMode |= constants.CAN_EXMODE_FASTDATA

        _canlib.canControlInitialize(
            self._control_handle,
            bOpMode,
            bExMode,
            constants.CAN_FILTER_PASS,
            constants.CAN_FILTER_PASS,
            0,
            0,
            ctypes.byref(pBtpSDR),
            ctypes.byref(pBtpFDR),
        )

        # With receive messages, this field contains the relative reception time of
        # the message in ticks. The resolution of a tick can be calculated from the fields
        # dwClockFreq and dwTscDivisor of the structure  CANCAPABILITIES in accordance with the following formula:
        # frequency [1/s] = dwClockFreq / dwTscDivisor
        # We explicitly cast to float for Python 2.x users
        self._tick_resolution = float(
            self._channel_capabilities.dwTscClkFreq  # TODO confirm
            / self._channel_capabilities.dwTscDivisor
        )

        # Setup filters before starting the channel
        if can_filters:
            log.info("The IXXAT VCI backend is filtering messages")
            # Disable every message coming in
            for extended in (0, 1):
                _canlib.canControlSetAccFilter(
                    self._control_handle,
                    extended,
                    constants.CAN_ACC_CODE_NONE,
                    constants.CAN_ACC_MASK_NONE,
                )
            for can_filter in can_filters:
                # Filters define what messages are accepted
                code = int(can_filter["can_id"])
                mask = int(can_filter["can_mask"])
                extended = can_filter.get("extended", False)
                _canlib.canControlAddFilterIds(
                    self._control_handle, 1 if extended else 0, code << 1, mask << 1
                )
                log.info("Accepting ID: 0x%X MASK: 0x%X", code, mask)

        # Start the CAN controller. Messages will be forwarded to the channel
        _canlib.canControlStart(self._control_handle, constants.TRUE)

        # For cyclic transmit list. Set when .send_periodic() is first called
        self._scheduler = None
        self._scheduler_resolution = None
        self.channel = channel

        # Usually you get back 3 messages like "CAN initialized" ecc...
        # Clear the FIFO by filter them out with low timeout
        for _ in range(rxFifoSize):
            try:
                _canlib.canChannelReadMessage(
                    self._channel_handle, 0, ctypes.byref(self._message)
                )
            except (VCITimeout, VCIRxQueueEmptyError):
                break

        super().__init__(channel=channel, can_filters=None, **kwargs)

    def _inWaiting(self):
        try:
            _canlib.canChannelWaitRxEvent(self._channel_handle, 0)
        except VCITimeout:
            return 0
        else:
            return 1

    def flush_tx_buffer(self):
        """Flushes the transmit buffer on the IXXAT"""
        # TODO #64: no timeout?
        _canlib.canChannelWaitTxEvent(self._channel_handle, constants.INFINITE)

    def _recv_internal(self, timeout):
        """Read a message from IXXAT device."""

        # TODO: handling CAN error messages?
        data_received = False

        if timeout == 0:
            # Peek without waiting
            try:
                _canlib.canChannelPeekMessage(
                    self._channel_handle, ctypes.byref(self._message)
                )
            except (VCITimeout, VCIRxQueueEmptyError, VCIError):
                # VCIError means no frame available (canChannelPeekMessage returned different from zero)
                return None, True
            else:
                if self._message.uMsgInfo.Bits.type == constants.CAN_MSGTYPE_DATA:
                    data_received = True
        else:
            # Wait if no message available
            if timeout is None or timeout < 0:
                remaining_ms = constants.INFINITE
                t0 = None
            else:
                timeout_ms = int(timeout * 1000)
                remaining_ms = timeout_ms
                t0 = _timer_function()

            while True:
                try:
                    _canlib.canChannelReadMessage(
                        self._channel_handle, remaining_ms, ctypes.byref(self._message)
                    )
                except (VCITimeout, VCIRxQueueEmptyError):
                    # Ignore the 2 errors, the timeout is handled manually with the _timer_function()
                    pass
                else:
                    # See if we got a data or info/error messages
                    if self._message.uMsgInfo.Bits.type == constants.CAN_MSGTYPE_DATA:
                        data_received = True
                        break
                    elif self._message.uMsgInfo.Bits.type == constants.CAN_MSGTYPE_INFO:
                        log.info(
                            CAN_INFO_MESSAGES.get(
                                self._message.abData[0],
                                "Unknown CAN info message code {}".format(
                                    self._message.abData[0]
                                ),
                            )
                        )

                    elif (
                        self._message.uMsgInfo.Bits.type == constants.CAN_MSGTYPE_ERROR
                    ):
                        log.warning(
                            CAN_ERROR_MESSAGES.get(
                                self._message.abData[0],
                                "Unknown CAN error message code {}".format(
                                    self._message.abData[0]
                                ),
                            )
                        )

                    elif (
                        self._message.uMsgInfo.Bits.type == constants.CAN_MSGTYPE_STATUS
                    ):
                        log.info(_format_can_status(self._message.abData[0]))
                        if self._message.abData[0] & constants.CAN_STATUS_BUSOFF:
                            raise VCIBusOffError()

                    elif (
                        self._message.uMsgInfo.Bits.type
                        == constants.CAN_MSGTYPE_TIMEOVR
                    ):
                        pass
                    else:
                        log.warning("Unexpected message info type")

                if t0 is not None:
                    remaining_ms = timeout_ms - int((_timer_function() - t0) * 1000)
                    if remaining_ms < 0:
                        break

        if not data_received:
            # Timed out / can message type is not DATA
            return None, True

        data_len = can.util.dlc2len(self._message.uMsgInfo.Bits.dlc)
        # The _message.dwTime is a 32bit tick value and will overrun,
        # so expect to see the value restarting from 0
        rx_msg = Message(
            timestamp=self._message.dwTime
            / self._tick_resolution,  # Relative time in s
            is_remote_frame=bool(self._message.uMsgInfo.Bits.rtr),
            is_extended_id=bool(self._message.uMsgInfo.Bits.ext),
            arbitration_id=self._message.dwMsgId,
            dlc=data_len,
            data=self._message.abData[:data_len],
            channel=self.channel,
        )

        return rx_msg, True

    def send(self, msg: Message, timeout: Optional[float] = None) -> None:
        """
        Sends a message on the bus. The interface may buffer the message.

        :param msg:
            The message to send.
        :param timeout:
            Timeout after some time.
        :raise:
            :class:CanTimeoutError
            :class:CanOperationError
        """
        # This system is not designed to be very efficient
        message = structures.CANMSG2()
        message.uMsgInfo.Bits.type = constants.CAN_MSGTYPE_DATA
        message.uMsgInfo.Bits.rtr = 1 if msg.is_remote_frame else 0
        message.uMsgInfo.Bits.ext = 1 if msg.is_extended_id else 0
        message.uMsgInfo.Bits.srr = 1 if self._receive_own_messages else 0
        message.uMsgInfo.Bits.fdr = 1 if msg.bitrate_switch else 0
        message.uMsgInfo.Bits.edl = 1 if msg.is_fd else 0
        message.dwMsgId = msg.arbitration_id
        if msg.dlc:  # this dlc means number of bytes of payload
            message.uMsgInfo.Bits.dlc = can.util.len2dlc(msg.dlc)
            data_len_dif = msg.dlc - len(msg.data)
            data = msg.data + bytearray(
                [0] * data_len_dif
            )  # pad with zeros until required length
            adapter = (ctypes.c_uint8 * msg.dlc).from_buffer(data)
            ctypes.memmove(message.abData, adapter, msg.dlc)

        if timeout:
            _canlib.canChannelSendMessage(
                self._channel_handle, int(timeout * 1000), message
            )

        else:
            _canlib.canChannelPostMessage(self._channel_handle, message)

    def _send_periodic_internal(self, msg, period, duration=None):
        """Send a message using built-in cyclic transmit list functionality."""
        if self._scheduler is None:
            self._scheduler = HANDLE()
            _canlib.canSchedulerOpen(self._device_handle, self.channel, self._scheduler)
            caps = structures.CANCAPABILITIES2()
            _canlib.canSchedulerGetCaps(self._scheduler, caps)
            self._scheduler_resolution = (
                float(caps.dwCmsClkFreq) / caps.dwCmsDivisor
            )  # TODO: confirm
            _canlib.canSchedulerActivate(self._scheduler, constants.TRUE)
        return CyclicSendTask(
            self._scheduler, msg, period, duration, self._scheduler_resolution
        )

    def shutdown(self):
        if self._scheduler is not None:
            _canlib.canSchedulerClose(self._scheduler)
        _canlib.canChannelClose(self._channel_handle)
        _canlib.canControlStart(self._control_handle, constants.FALSE)
        _canlib.canControlClose(self._control_handle)
        _canlib.vciDeviceClose(self._device_handle)


class CyclicSendTask(LimitedDurationCyclicSendTaskABC, RestartableCyclicTaskABC):
    """A message in the cyclic transmit list."""

    def __init__(self, scheduler, msgs, period, duration, resolution):
        super().__init__(msgs, period, duration)
        if len(self.messages) != 1:
            raise ValueError(
                "IXXAT Interface only supports periodic transmission of 1 element"
            )

        self._scheduler = scheduler
        self._index = None
        self._count = int(duration / period) if duration else 0

        self._msg = structures.CANCYCLICTXMSG2()
        self._msg.wCycleTime = int(round(period * resolution))
        self._msg.dwMsgId = self.messages[0].arbitration_id
        self._msg.uMsgInfo.Bits.type = constants.CAN_MSGTYPE_DATA
        self._msg.uMsgInfo.Bits.ext = 1 if self.messages[0].is_extended_id else 0
        self._msg.uMsgInfo.Bits.rtr = 1 if self.messages[0].is_remote_frame else 0
        self._msg.uMsgInfo.Bits.dlc = self.messages[0].dlc
        for i, b in enumerate(self.messages[0].data):
            self._msg.abData[i] = b
        self.start()

    def start(self):
        """Start transmitting message (add to list if needed)."""
        if self._index is None:
            self._index = ctypes.c_uint32()
            _canlib.canSchedulerAddMessage(self._scheduler, self._msg, self._index)
        _canlib.canSchedulerStartMessage(self._scheduler, self._index, self._count)

    def pause(self):
        """Pause transmitting message (keep it in the list)."""
        _canlib.canSchedulerStopMessage(self._scheduler, self._index)

    def stop(self):
        """Stop transmitting message (remove from list)."""
        # Remove it completely instead of just stopping it to avoid filling up
        # the list with permanently stopped messages
        _canlib.canSchedulerRemMessage(self._scheduler, self._index)
        self._index = None


def _format_can_status(status_flags: int):
    """
    Format a status bitfield found in CAN_MSGTYPE_STATUS messages or in dwStatus
    field in CANLINESTATUS.

    Valid states are defined in the CAN_STATUS_* constants in cantype.h
    """
    states = []
    for flag, description in CAN_STATUS_FLAGS.items():
        if status_flags & flag:
            states.append(description)
            status_flags &= ~flag

    if status_flags:
        states.append("unknown state 0x{:02x}".format(status_flags))

    if states:
        return "CAN status message: {}".format(", ".join(states))
    else:
        return "Empty CAN status message"


def get_ixxat_hwids():
    """Get a list of hardware ids of all available IXXAT devices."""
    hwids = []
    device_handle = HANDLE()
    device_info = structures.VCIDEVICEINFO()

    _canlib.vciEnumDeviceOpen(ctypes.byref(device_handle))
    while True:
        try:
            _canlib.vciEnumDeviceNext(device_handle, ctypes.byref(device_info))
        except StopIteration:
            break
        else:
            hwids.append(device_info.UniqueHardwareId.AsChar.decode("ascii"))
    _canlib.vciEnumDeviceClose(device_handle)

    return hwids
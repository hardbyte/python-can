"""
Ctypes wrapper module for IXXAT Virtual CAN Interface V4 on win32 systems

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
import time
import warnings
from typing import Callable, List, Optional, Sequence, Tuple, Union

from can import (
    BitTiming,
    BitTimingFd,
    BusABC,
    BusState,
    CanProtocol,
    CyclicSendTaskABC,
    LimitedDurationCyclicSendTaskABC,
    Message,
    RestartableCyclicTaskABC,
)
from can.ctypesutil import HANDLE, PHANDLE, CLibrary
from can.ctypesutil import HRESULT as ctypes_HRESULT
from can.exceptions import CanInitializationError, CanInterfaceNotImplementedError
from can.interfaces.ixxat import constants, structures
from can.interfaces.ixxat.exceptions import *
from can.typechecking import AutoDetectedConfig, CanFilters
from can.util import deprecated_args_alias, dlc2len, len2dlc

__all__ = [
    "VCITimeout",
    "VCIError",
    "VCIBusOffError",
    "VCIDeviceNotFoundError",
    "IXXATBus",
    "vciFormatError",
]

log = logging.getLogger("can.ixxat")

# Hack to have vciFormatError as a free function, see below
vciFormatError = None

# main ctypes instance
_canlib = None
# TODO: Use ECI driver for linux
if sys.platform in ("win32", "cygwin"):
    try:
        _canlib = CLibrary("vcinpl2.dll")
    except Exception as e:
        log.warning("Cannot load IXXAT vcinpl library: %s", e)
else:
    # Will not work on other systems, but have it importable anyway for
    # tests/sphinx
    log.warning("IXXAT VCI library does not work on %s platform", sys.platform)


def __vciFormatErrorExtended(
    library_instance: CLibrary, function: Callable, vret: int, args: Tuple
):
    """Format a VCI error and attach failed function, decoded HRESULT and arguments
    :param CLibrary library_instance:
        Mapped instance of IXXAT vcinpl library
    :param callable function:
        Failed function
    :param HRESULT vret:
        HRESULT returned by vcinpl call
    :param args:
        Arbitrary arguments tuple
    :return:
        Formatted string
    """
    # TODO: make sure we don't generate another exception
    return (
        "{__vciFormatError(library_instance, function, vret)} - arguments were {args}"
    )


def __vciFormatError(library_instance: CLibrary, function: Callable, vret: int):
    """Format a VCI error and attach failed function and decoded HRESULT
    :param CLibrary library_instance:
        Mapped instance of IXXAT vcinpl library
    :param callable function:
        Failed function
    :param HRESULT vret:
        HRESULT returned by vcinpl call
    :return:
        Formatted string
    """
    buf = ctypes.create_string_buffer(constants.VCI_MAX_ERRSTRLEN)
    ctypes.memset(buf, 0, constants.VCI_MAX_ERRSTRLEN)
    library_instance.vciFormatError(vret, buf, constants.VCI_MAX_ERRSTRLEN)
    return f"function {function._name} failed ({buf.value.decode('utf-8', 'replace')})"


def __check_status(result: int, function: Callable, args: Tuple):
    """
    Check the result of a vcinpl function call and raise appropriate exception
    in case of an error. Used as errcheck function when mapping C functions
    with ctypes.
        :param result:
            Function call numeric result
        :param callable function:
            Called function
        :param args:
            Arbitrary arguments tuple
        :raise:
            :class:VCITimeout
            :class:VCIRxQueueEmptyError
            :class:StopIteration
            :class:VCIError
    """
    if result == constants.VCI_E_TIMEOUT:
        raise VCITimeout(f"Function {function._name} timed out")
    elif result == constants.VCI_E_RXQUEUE_EMPTY:
        raise VCIRxQueueEmptyError()
    elif result == constants.VCI_E_NO_MORE_ITEMS:
        raise StopIteration()
    elif result == constants.VCI_E_ACCESSDENIED:
        log.warning(
            f"VCI_E_ACCESSDENIED error raised when calling VCI Function {function._name}"
        )
        # not a real error, might happen if another program has initialized the bus
    elif result != constants.VCI_OK:
        raise VCIError(vciFormatError(function, result))

    return result


try:
    hresult_type = ctypes.c_ulong
    # Map all required symbols and initialize library ---------------------------
    # HRESULT VCIAPI vciInitialize ( void );
    _canlib.map_symbol("vciInitialize", hresult_type, (), __check_status)

    # void VCIAPI vciFormatError (HRESULT hrError, PCHAR pszText, UINT32 dwsize);
    try:
        _canlib.map_symbol(
            "vciFormatError", None, (ctypes_HRESULT, ctypes.c_char_p, ctypes.c_uint32)
        )
    except ImportError:
        _canlib.map_symbol(
            "vciFormatErrorA", None, (ctypes_HRESULT, ctypes.c_char_p, ctypes.c_uint32)
        )
        _canlib.vciFormatError = _canlib.vciFormatErrorA
    # Hack to have vciFormatError as a free function
    vciFormatError = functools.partial(__vciFormatError, _canlib)

    # HRESULT VCIAPI vciEnumDeviceOpen( OUT PHANDLE hEnum );
    _canlib.map_symbol("vciEnumDeviceOpen", hresult_type, (PHANDLE,), __check_status)
    # HRESULT VCIAPI vciEnumDeviceClose ( IN HANDLE hEnum );
    _canlib.map_symbol("vciEnumDeviceClose", hresult_type, (HANDLE,), __check_status)
    # HRESULT VCIAPI vciEnumDeviceNext( IN  HANDLE hEnum, OUT PVCIDEVICEINFO pInfo );
    _canlib.map_symbol(
        "vciEnumDeviceNext",
        hresult_type,
        (HANDLE, structures.PVCIDEVICEINFO),
        __check_status,
    )

    # HRESULT VCIAPI vciDeviceOpen( IN  REFVCIID rVciid, OUT PHANDLE  phDevice );
    _canlib.map_symbol(
        "vciDeviceOpen", hresult_type, (structures.PVCIID, PHANDLE), __check_status
    )
    # HRESULT vciDeviceClose( HANDLE hDevice )
    _canlib.map_symbol("vciDeviceClose", hresult_type, (HANDLE,), __check_status)

    # HRESULT VCIAPI canChannelOpen( IN  HANDLE  hDevice, IN  UINT32  dwCanNo, IN  BOOL fExclusive, OUT PHANDLE phCanChn );
    _canlib.map_symbol(
        "canChannelOpen",
        hresult_type,
        (HANDLE, ctypes.c_uint32, ctypes.c_long, PHANDLE),
        __check_status,
    )
    # EXTERN_C HRESULT VCIAPI
    #   canChannelInitialize( IN HANDLE hCanChn,
    #                         IN UINT16 wRxFifoSize,
    #                         IN UINT16 wRxThreshold,
    #                         IN UINT16 wTxFifoSize,
    #                         IN UINT16 wTxThreshold,
    #                         IN UINT32 dwFilterSize,
    #                         IN UINT8  bFilterMode );
    _canlib.map_symbol(
        "canChannelInitialize",
        hresult_type,
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
        "canChannelActivate", hresult_type, (HANDLE, ctypes.c_long), __check_status
    )
    # HRESULT canChannelClose( HANDLE hChannel )
    _canlib.map_symbol("canChannelClose", hresult_type, (HANDLE,), __check_status)
    # EXTERN_C HRESULT VCIAPI canChannelReadMessage( IN  HANDLE  hCanChn, IN  UINT32  dwMsTimeout, OUT PCANMSG2 pCanMsg );
    _canlib.map_symbol(
        "canChannelReadMessage",
        hresult_type,
        (HANDLE, ctypes.c_uint32, structures.PCANMSG2),
        __check_status,
    )
    # HRESULT canChannelPeekMessage(HANDLE hChannel,PCANMSG2 pCanMsg );
    _canlib.map_symbol(
        "canChannelPeekMessage",
        hresult_type,
        (HANDLE, structures.PCANMSG2),
        __check_status,
    )
    # HRESULT canChannelWaitTxEvent (HANDLE hChannel UINT32 dwMsTimeout );
    _canlib.map_symbol(
        "canChannelWaitTxEvent",
        hresult_type,
        (HANDLE, ctypes.c_uint32),
        __check_status,
    )
    # HRESULT canChannelWaitRxEvent (HANDLE hChannel, UINT32 dwMsTimeout );
    _canlib.map_symbol(
        "canChannelWaitRxEvent",
        hresult_type,
        (HANDLE, ctypes.c_uint32),
        __check_status,
    )
    # HRESULT canChannelPostMessage (HANDLE hChannel, PCANMSG2 pCanMsg );
    _canlib.map_symbol(
        "canChannelPostMessage",
        hresult_type,
        (HANDLE, structures.PCANMSG2),
        __check_status,
    )
    # HRESULT canChannelSendMessage (HANDLE hChannel, UINT32 dwMsTimeout, PCANMSG2 pCanMsg );
    _canlib.map_symbol(
        "canChannelSendMessage",
        hresult_type,
        (HANDLE, ctypes.c_uint32, structures.PCANMSG2),
        __check_status,
    )

    # EXTERN_C HRESULT VCIAPI canControlOpen( IN  HANDLE  hDevice, IN  UINT32  dwCanNo, OUT PHANDLE phCanCtl );
    _canlib.map_symbol(
        "canControlOpen",
        hresult_type,
        (HANDLE, ctypes.c_uint32, PHANDLE),
        __check_status,
    )
    # EXTERN_C HRESULT VCIAPI
    #   canControlInitialize( IN HANDLE  hCanCtl,
    #                         IN UINT8   bOpMode,
    #                         IN UINT8   bExMode,
    #                         IN UINT8   bSFMode,
    #                         IN UINT8   bEFMode,
    #                         IN UINT32  dwSFIds,
    #                         IN UINT32  dwEFIds,
    #                         IN PCANBTP pBtpSDR,
    #                         IN PCANBTP pBtpFDR );
    _canlib.map_symbol(
        "canControlInitialize",
        hresult_type,
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
    _canlib.map_symbol("canControlClose", hresult_type, (HANDLE,), __check_status)
    # EXTERN_C HRESULT VCIAPI canControlReset( IN HANDLE hCanCtl );
    _canlib.map_symbol("canControlReset", hresult_type, (HANDLE,), __check_status)
    # EXTERN_C HRESULT VCIAPI canControlStart( IN HANDLE hCanCtl, IN BOOL   fStart );
    _canlib.map_symbol(
        "canControlStart", hresult_type, (HANDLE, ctypes.c_long), __check_status
    )
    # EXTERN_C HRESULT VCIAPI canControlGetStatus( IN  HANDLE hCanCtl, OUT PCANLINESTATUS2 pStatus );
    _canlib.map_symbol(
        "canControlGetStatus",
        hresult_type,
        (HANDLE, structures.PCANLINESTATUS2),
        __check_status,
    )
    # EXTERN_C HRESULT VCIAPI canControlGetCaps( IN  HANDLE hCanCtl, OUT PCANCAPABILITIES2 pCanCaps );
    _canlib.map_symbol(
        "canControlGetCaps",
        hresult_type,
        (HANDLE, structures.PCANCAPABILITIES2),
        __check_status,
    )
    # EXTERN_C HRESULT VCIAPI canControlSetAccFilter( IN HANDLE hCanCtl, IN BOOL   fExtend, IN UINT32 dwCode, IN UINT32 dwMask );
    _canlib.map_symbol(
        "canControlSetAccFilter",
        hresult_type,
        (HANDLE, ctypes.c_int, ctypes.c_uint32, ctypes.c_uint32),
        __check_status,
    )
    # EXTERN_C HRESULT canControlAddFilterIds (HANDLE hControl, BOOL fExtended, UINT32 dwCode, UINT32 dwMask);
    _canlib.map_symbol(
        "canControlAddFilterIds",
        hresult_type,
        (HANDLE, ctypes.c_int, ctypes.c_uint32, ctypes.c_uint32),
        __check_status,
    )
    # EXTERN_C HRESULT canControlRemFilterIds (HANDLE hControl, BOOL fExtendend, UINT32 dwCode, UINT32 dwMask );
    _canlib.map_symbol(
        "canControlRemFilterIds",
        hresult_type,
        (HANDLE, ctypes.c_int, ctypes.c_uint32, ctypes.c_uint32),
        __check_status,
    )
    # EXTERN_C HRESULT canSchedulerOpen (HANDLE hDevice, UINT32 dwCanNo, PHANDLE phScheduler );
    _canlib.map_symbol(
        "canSchedulerOpen",
        hresult_type,
        (HANDLE, ctypes.c_uint32, PHANDLE),
        __check_status,
    )
    # EXTERN_C HRESULT canSchedulerClose (HANDLE hScheduler );
    _canlib.map_symbol("canSchedulerClose", hresult_type, (HANDLE,), __check_status)
    # EXTERN_C HRESULT canSchedulerGetCaps (HANDLE hScheduler, PCANCAPABILITIES2 pCaps );
    _canlib.map_symbol(
        "canSchedulerGetCaps",
        hresult_type,
        (HANDLE, structures.PCANCAPABILITIES2),
        __check_status,
    )
    # EXTERN_C HRESULT canSchedulerActivate ( HANDLE hScheduler, BOOL fEnable );
    _canlib.map_symbol(
        "canSchedulerActivate", hresult_type, (HANDLE, ctypes.c_int), __check_status
    )
    # EXTERN_C HRESULT canSchedulerAddMessage (HANDLE hScheduler, PCANCYCLICTXMSG2 pMessage, PUINT32 pdwIndex );
    _canlib.map_symbol(
        "canSchedulerAddMessage",
        hresult_type,
        (HANDLE, structures.PCANCYCLICTXMSG2, ctypes.POINTER(ctypes.c_uint32)),
        __check_status,
    )
    # EXTERN_C HRESULT canSchedulerRemMessage (HANDLE hScheduler, UINT32 dwIndex );
    _canlib.map_symbol(
        "canSchedulerRemMessage",
        hresult_type,
        (HANDLE, ctypes.c_uint32),
        __check_status,
    )
    # EXTERN_C HRESULT canSchedulerStartMessage (HANDLE hScheduler, UINT32 dwIndex, UINT16 dwCount );
    _canlib.map_symbol(
        "canSchedulerStartMessage",
        hresult_type,
        (HANDLE, ctypes.c_uint32, ctypes.c_uint16),
        __check_status,
    )
    # EXTERN_C HRESULT canSchedulerStopMessage (HANDLE hScheduler, UINT32 dwIndex );
    _canlib.map_symbol(
        "canSchedulerStopMessage",
        hresult_type,
        (HANDLE, ctypes.c_uint32),
        __check_status,
    )
    _canlib.vciInitialize()
except AttributeError:
    # In case _canlib == None meaning we're not on win32/no lib found
    pass
except Exception as exc:
    log.warning("Could not initialize IXXAT VCI library: %s", exc)


class IXXATBus(BusABC):
    """The CAN Bus implemented for the IXXAT interface.

    .. warning::

        This interface does implement efficient filtering of messages, but
        the filters have to be set in ``__init__`` using the ``can_filters`` parameter.
        Using :meth:`~can.BusABC.set_filters` does not work.

    """

    @deprecated_args_alias(
        deprecation_start="4.2.2",
        deprecation_end="5.0.0",
        sjw_abr=None,  # Use BitTiming class instead
        tseg1_abr=None,
        tseg2_abr=None,
        sjw_dbr=None,
        tseg1_dbr=None,
        tseg2_dbr=None,
        ssp_dbr=None,
    )
    @deprecated_args_alias(
        deprecation_start="4.0.0",
        deprecation_end="5.0.0",
        UniqueHardwareId="unique_hardware_id",
        rxFifoSize="rx_fifo_size",
        txFifoSize="tx_fifo_size",
    )
    def __init__(
        self,
        channel: int,
        can_filters: Optional[CanFilters] = None,
        receive_own_messages: Optional[int] = False,
        unique_hardware_id: Optional[int] = None,
        extended: Optional[bool] = True,
        fd: Optional[bool] = False,
        rx_fifo_size: Optional[int] = None,
        tx_fifo_size: Optional[int] = None,
        bitrate: Optional[int] = 500_000,
        data_bitrate: Optional[int] = 2_000_000,
        timing: Optional[Union[BitTiming, BitTimingFd]] = None,
        **kwargs,
    ):
        """
        :param channel:
            The Channel id to create this bus with.

        :param can_filters:
            See :meth:`can.BusABC.set_filters`.

        :param receive_own_messages:
            Enable self-reception of sent messages.

        :param unique_hardware_id:
            unique_hardware_id to connect (optional, will use the first found if not supplied)

        :param extended:
            Default True, enables the capability to use extended IDs.

        :param fd:
            Default False, enables CAN-FD usage (alternatively a :class:`~can.BitTimingFd`
            instance may be passed to the `timing` parameter).

        :param rx_fifo_size:
            Receive fifo size (default 16). If initialised as an FD bus, this value is automatically
            increased to 1024 unless a value is specified by the user.

        :param tx_fifo_size:
            Transmit fifo size (default 16). If initialised as an FD bus, this value is automatically
            increased to 128 unless a value is specified by the user.

        :param bitrate:
            Channel bitrate in bit/s.  Note that this value will be overriden if a
            :class:`~can.BitTiming` or :class:`~can.BitTimingFd` instance is provided
            in the `timing` parameter.

        :param data_bitrate:
            Channel bitrate in bit/s (only in CAN-Fd if baudrate switch enabled). Note that
            this value will be overriden if a :class:`~can.BitTimingFd` instance is provided
            in the `timing` parameter.

        :param timing:
            Optional :class:`~can.BitTiming` or :class:`~can.BitTimingFd` instance
            to use for custom bit timing setting. The `f_clock` value of the timing
            instance must be set to the appropriate value for the interface.
            If this parameter is provided, it takes precedence over all other optional
            timing-related parameters like `bitrate`, `data_bitrate` and `fd`.

        """
        if _canlib is None:
            raise CanInterfaceNotImplementedError(
                "The IXXAT VCI library has not been initialized. Check the logs for more details."
            )
        log.info("CAN Filters: %s", can_filters)

        # Configuration options
        if isinstance(timing, BitTiming):
            fd = False  # if a BitTiming instance has been passed, force the bus to initialise as a standard bus.
        elif isinstance(timing, BitTiming):
            fd = True  # if a BitTimingFd instance has been passed, force the bus to initialise as FD capble
        channel = int(channel)  # Usually comes as a string from the config file
        if channel < 0:
            raise ValueError("channel number must be >= 0")
        bitrate = int(bitrate)
        data_bitrate = int(data_bitrate)
        if (bitrate < 0) or (data_bitrate < 0):
            raise ValueError("bitrate and data_bitrate must be >= 0")
        if (bitrate > 1_000_000) or (data_bitrate > 10_000_000):
            raise ValueError(
                "bitrate must be <= 1_000_000 data_bitrate must be <= 10_000_000"
            )
        self.receive_own_messages = receive_own_messages

        # fetch deprecated timing arguments (if provided)
        tseg1_abr = kwargs.get("tseg1_abr")
        tseg2_abr = kwargs.get("tseg2_abr")
        sjw_abr = kwargs.get("sjw_abr")
        tseg1_dbr = kwargs.get("tseg1_dbr")
        tseg2_dbr = kwargs.get("tseg2_dbr")
        sjw_dbr = kwargs.get("sjw_dbr")
        ssp_dbr = kwargs.get("ssp_dbr")

        # setup buffer sizes
        if rx_fifo_size is not None:  # if the user provided an rx fifo size
            if rx_fifo_size <= 0:
                raise ValueError("rx_fifo_size must be > 0")
        else:  # otherwise use the default size (depending upon if FD or not)
            rx_fifo_size = 16
            if fd:
                rx_fifo_size = 1024

        if tx_fifo_size is not None:  # if the user provided a tx fifo size
            if tx_fifo_size <= 0:
                raise ValueError("tx_fifo_size must be > 0")
        else:  # otherwise use the default size (depending upon if FD or not)
            tx_fifo_size = 16
            if fd:
                tx_fifo_size = 128

        self._device_handle = HANDLE()
        self._device_info = structures.VCIDEVICEINFO()
        self._control_handle = HANDLE()
        self._channel_handle = HANDLE()
        self._channel_capabilities = structures.CANCAPABILITIES2()
        self._message = structures.CANMSG2()
        if fd:
            self._payload = (ctypes.c_byte * 64)()
        else:
            self._payload = (ctypes.c_byte * 8)()

        # Search for supplied device
        if unique_hardware_id is None:
            log.info("Searching for first available device")
        else:
            log.info("Searching for unique HW ID %s", unique_hardware_id)
        _canlib.vciEnumDeviceOpen(ctypes.byref(self._device_handle))
        while True:
            try:
                _canlib.vciEnumDeviceNext(
                    self._device_handle, ctypes.byref(self._device_info)
                )
            except StopIteration as exc:
                if unique_hardware_id is None:
                    raise VCIDeviceNotFoundError(
                        "No IXXAT device(s) connected or device(s) in use by other process(es)."
                    ) from exc
                else:
                    raise VCIDeviceNotFoundError(
                        f"Unique HW ID {unique_hardware_id} not connected or not available."
                    ) from exc
            else:
                if (unique_hardware_id is None) or (
                    self._device_info.UniqueHardwareId.AsChar
                    == bytes(unique_hardware_id, "ascii")
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
        except Exception as exc:
            raise CanInitializationError(f"Could not open device: {exc}") from exc

        log.info("Using unique HW ID %s", self._device_info.UniqueHardwareId.AsChar)

        log.info(
            "Initializing channel %d in shared mode, %d rx buffers, %d tx buffers",
            channel,
            rx_fifo_size,
            tx_fifo_size,
        )

        try:
            _canlib.canChannelOpen(
                self._device_handle,
                channel,
                constants.FALSE,
                ctypes.byref(self._channel_handle),
            )
        except Exception as exc:
            raise CanInitializationError(
                f"Could not open and initialize channel: {exc}"
            ) from exc

        # Signal TX/RX events when at least one frame has been handled
        _canlib.canChannelInitialize(
            self._channel_handle,
            rx_fifo_size,
            1,
            tx_fifo_size,
            1,
            0,
            constants.CAN_FILTER_PASS,
        )
        _canlib.canChannelActivate(self._channel_handle, constants.TRUE)

        _canlib.canControlOpen(
            self._device_handle, channel, ctypes.byref(self._control_handle)
        )

        log.debug("Fetching capabilities for interface channel %d", channel)
        _canlib.canControlGetCaps(
            self._control_handle, ctypes.byref(self._channel_capabilities)
        )

        # check capabilities
        bOpMode = constants.CAN_OPMODE_UNDEFINED
        if (
            self._channel_capabilities.dwFeatures & constants.CAN_FEATURE_STDANDEXT
        ) != 0:
            # controller supports CAN_OPMODE_STANDARD and CAN_OPMODE_EXTENDED at the same time
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
            # controller supports either CAN_OPMODE_STANDARD or CAN_OPMODE_EXTENDED, but not both simultaneously
            bOpMode |= (
                constants.CAN_OPMODE_EXTENDED
                if extended
                else constants.CAN_OPMODE_STANDARD
            )

        if (  # controller supports receiving error frames:
            self._channel_capabilities.dwFeatures & constants.CAN_FEATURE_ERRFRAME
        ) != 0:
            bOpMode |= constants.CAN_OPMODE_ERRFRAME

        if (  # controller supports receiving error frames:
            self._channel_capabilities.dwFeatures & constants.CAN_FEATURE_BUSLOAD
        ) != 0:
            self._bus_load_calculation = True
        else:
            self._bus_load_calculation = False

        if (  # controller supports hardware scheduling of cyclic messages
            self._channel_capabilities.dwFeatures & constants.CAN_FEATURE_SCHEDULER
        ) != 0:
            self._interface_scheduler_capable = True
        else:
            self._interface_scheduler_capable = False

        bExMode = constants.CAN_EXMODE_DISABLED
        self._can_protocol = CanProtocol.CAN_20  # default to standard CAN protocol
        if fd:
            if (
                self._channel_capabilities.dwFeatures & constants.CAN_FEATURE_EXTDATA
            ) != 0:
                bExMode |= constants.CAN_EXMODE_EXTDATALEN
            else:
                raise CanInitializationError(
                    "The interface %s does not support extended data frames (FD)"
                    % self._device_info.UniqueHardwareId.AsChar.decode("ascii"),
                )
            if (
                self._channel_capabilities.dwFeatures & constants.CAN_FEATURE_FASTDATA
            ) != 0:
                bExMode |= constants.CAN_EXMODE_FASTDATA
            else:
                raise CanInitializationError(
                    "The interface %s does not support fast data rates (FD)"
                    % self._device_info.UniqueHardwareId.AsChar.decode("ascii"),
                )
            # set bus to CAN FD protocol once FD capability is verified
            self._can_protocol = CanProtocol.CAN_FD

        if timing and not isinstance(timing, (BitTiming, BitTimingFd)):
            raise CanInitializationError(
                "The timing parameter to the Ixxat Bus must be None, or an instance of can.BitTiming or can.BitTimingFd"
            )

        pBtpSDR, pBtpFDR = self._bit_timing_constructor(
            timing,
            bitrate,
            tseg1_abr,  # deprecated
            tseg2_abr,  # deprecated
            sjw_abr,  # deprecated
            data_bitrate,
            tseg1_dbr,  # deprecated
            tseg2_dbr,  # deprecated
            sjw_dbr,  # deprecated
            ssp_dbr,  # deprecated
        )

        log.info(
            "Initialising Channel %d with the following parameters:  \n%s\n%s",
            channel,
            pBtpSDR,
            pBtpFDR,
        )

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
        self._tick_resolution = (
            self._channel_capabilities.dwTscClkFreq
            / self._channel_capabilities.dwTscDivisor
        )

        # Setup filters before starting the channel
        if can_filters:
            log.info("The IXXAT VCI backend is filtering messages")
            # Disable every message coming in
            for extended_filter in (False, True):
                _canlib.canControlSetAccFilter(
                    self._control_handle,
                    extended_filter,
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
        for _ in range(rx_fifo_size):
            try:
                _canlib.canChannelReadMessage(
                    self._channel_handle, 0, ctypes.byref(self._message)
                )
            except (VCITimeout, VCIRxQueueEmptyError):
                break

        # TODO - it should be possible to implement a query to the VCI driver to check if there is an existing
        # open handle to the VCI comms layer (either from python-can or another program). This would be worth
        # implementing as an open handle with an active bus will prevent the bitrate from being altered.

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
                t0 = time.perf_counter()

            while True:
                try:
                    _canlib.canChannelReadMessage(
                        self._channel_handle, remaining_ms, ctypes.byref(self._message)
                    )
                except (VCITimeout, VCIRxQueueEmptyError):
                    # Ignore the 2 errors, the timeout is handled manually with the perf_counter()
                    pass
                else:
                    # See if we got a data or info/error messages
                    if self._message.uMsgInfo.Bits.type == constants.CAN_MSGTYPE_DATA:
                        data_received = True
                        break
                    if self._message.uMsgInfo.Bits.type == constants.CAN_MSGTYPE_INFO:
                        log.info(
                            constants.CAN_INFO_MESSAGES.get(
                                self._message.abData[0],
                                f"Unknown CAN info message code {self._message.abData[0]}",
                            )
                        )

                    elif (
                        self._message.uMsgInfo.Bits.type == constants.CAN_MSGTYPE_ERROR
                    ):
                        log.warning(
                            constants.CAN_ERROR_MESSAGES.get(
                                self._message.abData[0],
                                f"Unknown CAN error message code {self._message.abData[0]}",
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
                    remaining_ms = timeout_ms - int((time.perf_counter() - t0) * 1000)
                    if remaining_ms < 0:
                        break

        if not data_received:
            # Timed out / can message type is not DATA
            return None, True

        data_len = dlc2len(self._message.uMsgInfo.Bits.dlc)
        # The _message.dwTime is a 32bit tick value and will overrun,
        # so expect to see the value restarting from 0
        rx_msg = Message(
            timestamp=self._message.dwTime
            / self._tick_resolution,  # Relative time in s
            is_remote_frame=bool(self._message.uMsgInfo.Bits.rtr),
            is_fd=bool(self._message.uMsgInfo.Bits.edl),
            is_rx=True,
            is_error_frame=bool(
                self._message.uMsgInfo.Bits.type == constants.CAN_MSGTYPE_ERROR
            ),
            bitrate_switch=bool(self._message.uMsgInfo.Bits.fdr),
            error_state_indicator=bool(self._message.uMsgInfo.Bits.esi),
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
        message.uMsgInfo.Bits.type = (
            constants.CAN_MSGTYPE_ERROR
            if msg.is_error_frame
            else constants.CAN_MSGTYPE_DATA
        )
        message.uMsgInfo.Bits.rtr = 1 if msg.is_remote_frame else 0
        message.uMsgInfo.Bits.ext = 1 if msg.is_extended_id else 0
        message.uMsgInfo.Bits.srr = 1 if self.receive_own_messages else 0
        message.uMsgInfo.Bits.fdr = 1 if msg.bitrate_switch else 0
        message.uMsgInfo.Bits.esi = 1 if msg.error_state_indicator else 0
        message.uMsgInfo.Bits.edl = 1 if msg.is_fd else 0
        message.dwMsgId = msg.arbitration_id
        if msg.dlc:  # this dlc means number of bytes of payload
            message.uMsgInfo.Bits.dlc = len2dlc(msg.dlc)
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

    def _send_periodic_internal(
        self,
        msgs: Union[Sequence[Message], Message],
        period: float,
        duration: Optional[float] = None,
        modifier_callback: Optional[Callable[[Message], None]] = None,
    ) -> CyclicSendTaskABC:
        """Send a message using built-in cyclic transmit list functionality."""
        if modifier_callback is None:
            if self._interface_scheduler_capable:  # address issue #1121
                if self._scheduler is None:
                    self._scheduler = HANDLE()
                    _canlib.canSchedulerOpen(
                        self._device_handle, self.channel, self._scheduler
                    )
                    caps = structures.CANCAPABILITIES2()
                    _canlib.canSchedulerGetCaps(self._scheduler, caps)
                    self._scheduler_resolution = (
                        caps.dwCmsClkFreq / caps.dwCmsDivisor
                    )  # TODO: confirm
                    _canlib.canSchedulerActivate(self._scheduler, constants.TRUE)
                return CyclicSendTask(
                    self._scheduler,
                    msgs,
                    period,
                    duration,
                    self._scheduler_resolution,
                    self.receive_own_messages,
                )
            else:
                # fallback to thread based cyclic task
                warnings.warn(
                    "Falling back to a thread-based cyclic task:\n    The CAN_FEATURE_SCHEDULER flag is false for "
                    f"interface {self._device_info.UniqueHardwareId.AsChar.decode('ascii')}"
                )
        else:
            # fallback to thread based cyclic task
            warnings.warn(
                f"{self.__class__.__name__} falls back to a thread-based cyclic task, "
                "when the `modifier_callback` argument is given."
            )

        # return the BusABC periodic send task if the device is not scheduler capable or modifier_callback is used
        return BusABC._send_periodic_internal(
            self,
            msgs=msgs,
            period=period,
            duration=duration,
            modifier_callback=modifier_callback,
        )

    def shutdown(self):
        super().shutdown()
        if self._scheduler is not None:
            _canlib.canSchedulerClose(self._scheduler)
        _canlib.canChannelClose(self._channel_handle)
        _canlib.canControlStart(self._control_handle, constants.FALSE)
        _canlib.canControlReset(self._control_handle)
        _canlib.canControlClose(self._control_handle)
        _canlib.vciDeviceClose(self._device_handle)

    @property
    def clock_frequency(self) -> int:
        """
        :return: The can clock frequency of the attached adapter (e.g. for use in BitTiming)
        :rtype: int
        """
        return self._channel_capabilities.dwCanClkFreq

    @property
    def bus_load(self) -> int:
        """
        :return: The Bus Load in % (0 - 100) if the adapter is capable of measuring it.
         Otherwise returns 0 % with a warning message.
        :rtype: int
        """
        if self._bus_load_calculation:
            return self._status.bBusLoad
        else:
            warnings.warn("The current adapter does not support bus load measurement")
            return 0

    def _status(self) -> structures.CANLINESTATUS2:
        status = structures.CANLINESTATUS2()
        _canlib.canControlGetStatus(self._control_handle, ctypes.byref(status))
        return status

    @property
    def state(self) -> BusState:
        """
        Return the current state of the hardware
        """
        status = structures.CANLINESTATUS2()
        _canlib.canControlGetStatus(self._control_handle, ctypes.byref(status))
        if status.bOpMode & constants.CAN_OPMODE_LISTONLY:
            return BusState.PASSIVE

        error_byte_1 = status.dwStatus & 0x0F
        # CAN_STATUS_BUSOFF = 0x08  # bus off status
        if error_byte_1 & constants.CAN_STATUS_BUSOFF:
            return BusState.ERROR

        error_byte_2 = status.dwStatus & 0xF0
        # CAN_STATUS_BUSCERR  = 0x20  # bus coupling error
        if error_byte_2 & constants.CAN_STATUS_BUSCERR:
            raise BusState.ERROR

        return BusState.ACTIVE

    def _bit_timing_constructor(
        self,
        timing_obj: Optional[Union[BitTiming, BitTimingFd]],
        bitrate: Optional[int],
        tseg1_abr: Optional[int],
        tseg2_abr: Optional[int],
        sjw_abr: Optional[int],
        data_bitrate: Optional[int],
        tseg1_dbr: Optional[int],
        tseg2_dbr: Optional[int],
        sjw_dbr: Optional[int],
        ssp_dbr: Optional[int],
    ) -> Tuple:
        """
        A helper function to convert a can.BitTiming or can.BitTimingFd object into the arguments for
        the VCI driver's CANBTP function.
        :param timing_obj: A can.BitTiming or can.BitTimingFd instance. If this argument is specified,
         all other arguments are ignored
        :type timing_obj: Optional[Union[BitTiming, BitTimingFd]]
        :param bitrate: The standard / arbitration bitrate in bit/s.
        :type bitrate: Optional[int]
        :param tseg1_abr: Time segment 1 for the standard / arbitration speed, that is, the number of quanta from
         (but not including) the Sync Segment to the sampling point.
        :type tseg1_abr: Optional[int]
        :param tseg2_abr: Time segment 2 for the standard / arbitration speed, that is, the number of quanta from the
         sampling point to the end of the bit.
        :type tseg2_abr: Optional[int]
        :param sjw_abr: The Synchronization Jump Width for the standard / arbitration speed. Decides the maximum
         number of time quanta that the controller can resynchronize every bit.
        :type sjw_abr: Optional[int]
        :param data_bitrate: The CAN FD Data bitrate in bit/s.
        :type data_bitrate: Optional[int]
        :param tseg1_dbr: Time segment 1 for the CAN FD data speed, that is, the number of quanta from
         (but not including) the Sync Segment to the sampling point.
        :type tseg1_dbr: Optional[int]
        :param tseg2_dbr: Time segment 2 for the CAN FD data speed, that is, the number of quanta from the
         sampling point to the end of the bit.
        :type tseg2_dbr: Optional[int]
        :param sjw_dbr: The Synchronization Jump Width for the CAN FD data speed. Decides the maximum
         number of time quanta that the controller can resynchronize every bit.
        :type sjw_dbr: Optional[int]
        :param ssp_dbr: Secondary Sample Point Offset for the CAN FD data speed, that is, the number of quanta from
         (but not including) the Sync Segment to the secondary sampling point. If this value is not provided, it
          defaults to the same value as `tseg1_dbr`.
        :type ssp_dbr: Optional[int]
        :param : DESCRIPTION
        :type : TYPE
        :return: A Tuple containing two CANBTP structures for the VCI driver.
        The first is the standard CAN 2.0 CANBTP object (or the CAN FD Arbitration rate CANBTP object),
        and the second is the CAN FD data rate CANBTP object (which is null if a standard bus is initialised).
        :rtype: Tuple
        """

        # Create a null FD timing structure in case we are only using a standard bus
        pBtpFDR = structures.CANBTP(dwMode=0, dwBPS=0, wTS1=0, wTS2=0, wSJW=0, wTDO=0)

        # if only a bitrate is supplied
        if bitrate and not timing_obj and not (tseg1_abr and tseg2_abr and sjw_abr):
            # unless timing segments are specified, try and use a predefined set of timings from constants.py
            pBtpSDR = constants.CAN_BITRATE_PRESETS.get(bitrate, None)
            if not pBtpSDR:
                # if we have failed to identify a suitable set of timings from the presets
                timing_obj = BitTiming.from_sample_point(
                    f_clock=self._channel_capabilities.dwCanClkFreq,
                    bitrate=bitrate,
                    sample_point=80,
                )
        # if a bitrate and timings are supplied
        elif bitrate and not timing_obj and (tseg1_abr and tseg2_abr and sjw_abr):
            pBtpSDR = structures.CANBTP(
                dwMode=0,
                dwBPS=bitrate,
                wTS1=tseg1_abr,
                wTS2=tseg2_abr,
                wSJW=sjw_abr,
                wTDO=0,
            )

        # if a data_bitrate is supplied
        if (
            data_bitrate
            and not timing_obj
            and not (tseg1_dbr and tseg2_dbr and sjw_dbr)
        ):
            # unless timing segments are specified, try and use a predefined set of timings from constants.py
            pBtpFDR = constants.CAN_DATABITRATE_PRESETS.get(data_bitrate, None)
            if not pBtpFDR:
                # if we have failed to identify a suitable set of FD data timings from the presets
                timing_obj = BitTimingFd.from_sample_point(
                    f_clock=self._channel_capabilities.dwCanClkFreq,
                    nom_bitrate=bitrate,
                    nom_sample_point=80,  # 80%
                    data_bitrate=data_bitrate,
                    data_sample_point=80,  # 80%
                )
        # if a data_bitrate and timings are supplied
        elif data_bitrate and not timing_obj and (tseg1_dbr and tseg2_dbr and sjw_dbr):
            if not ssp_dbr:
                ssp_dbr = tseg2_dbr
            pBtpFDR = structures.CANBTP(
                dwMode=0,
                dwBPS=data_bitrate,
                wTS1=tseg1_dbr,
                wTS2=tseg2_dbr,
                wSJW=sjw_dbr,
                wTDO=ssp_dbr,
            )

        # if a timing object is provided
        if isinstance(timing_obj, BitTiming):
            pBtpSDR = structures.CANBTP(
                dwMode=0,
                dwBPS=timing_obj.bitrate,
                wTS1=timing_obj.tseg1,
                wTS2=timing_obj.tseg2,
                wSJW=timing_obj.sjw,
                wTDO=0,
            )
        elif isinstance(timing_obj, BitTimingFd):
            pBtpSDR = structures.CANBTP(
                dwMode=0,
                dwBPS=timing_obj.nom_bitrate,
                wTS1=timing_obj.nom_tseg1,
                wTS2=timing_obj.nom_tseg2,
                wSJW=timing_obj.nom_sjw,
                wTDO=0,
            )
            pBtpFDR = structures.CANBTP(
                dwMode=0,
                dwBPS=timing_obj.data_bitrate,
                wTS1=timing_obj.data_tseg1,
                wTS2=timing_obj.data_tseg2,
                wSJW=timing_obj.data_sjw,
                wTDO=timing_obj.data_tseg2,
            )

        return pBtpSDR, pBtpFDR

    @staticmethod
    def _detect_available_configs() -> List[AutoDetectedConfig]:
        config_list = []  # list in wich to store the resulting bus kwargs

        # used to detect HWID
        device_handle = HANDLE()
        device_info = structures.VCIDEVICEINFO()

        # used to attempt to open channels
        channel_handle = HANDLE()
        device_handle2 = HANDLE()

        try:
            _canlib.vciEnumDeviceOpen(ctypes.byref(device_handle))
            while True:
                try:
                    _canlib.vciEnumDeviceNext(device_handle, ctypes.byref(device_info))
                except StopIteration:
                    break
                else:
                    hwid = device_info.UniqueHardwareId.AsChar.decode("ascii")
                    _canlib.vciDeviceOpen(
                        ctypes.byref(device_info.VciObjectId),
                        ctypes.byref(device_handle2),
                    )
                    for channel in range(4):
                        try:
                            _canlib.canChannelOpen(
                                device_handle2,
                                channel,
                                constants.FALSE,
                                ctypes.byref(channel_handle),
                            )
                        except Exception:
                            # Array outside of bounds error == accessing a channel not in the hardware
                            break
                        else:
                            _canlib.canChannelClose(channel_handle)
                            config_list.append(
                                {
                                    "interface": "ixxat",
                                    "channel": channel,
                                    "unique_hardware_id": hwid,
                                }
                            )
                    _canlib.vciDeviceClose(device_handle2)
            _canlib.vciEnumDeviceClose(device_handle)
        except AttributeError:
            pass  # _canlib is None in the CI tests -> return a blank list

        return config_list


class CyclicSendTask(LimitedDurationCyclicSendTaskABC, RestartableCyclicTaskABC):
    """A message in the cyclic transmit list."""

    def __init__(
        self, scheduler, msgs, period, duration, resolution, receive_own_messages=False
    ):
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
        self._msg.uMsgInfo.Bits.srr = 1 if receive_own_messages else 0
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
    for flag, description in constants.CAN_STATUS_FLAGS.items():
        if status_flags & flag:
            states.append(description)
            status_flags &= ~flag

    if status_flags:
        states.append(f"unknown state 0x{status_flags:02x}")

    if states:
        return f"CAN status message: {', '.join(states)}"
    else:
        return "Empty CAN status message"


def get_ixxat_hwids():
    """Get a list of hardware ids of all available IXXAT devices."""
    hwids = []
    device_handle = HANDLE()
    device_info = structures.VCIDEVICEINFO()

    try:
        _canlib.vciEnumDeviceOpen(ctypes.byref(device_handle))
        while True:
            try:
                _canlib.vciEnumDeviceNext(device_handle, ctypes.byref(device_info))
            except StopIteration:
                break
            else:
                hwids.append(device_info.UniqueHardwareId.AsChar.decode("ascii"))
        _canlib.vciEnumDeviceClose(device_handle)
    except AttributeError:
        pass  # _canlib is None in the CI tests -> return a blank list

    return hwids

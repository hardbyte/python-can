import ctypes
import logging
from time import perf_counter
from typing import List, Optional, Tuple
from can import BusABC, Message
from can.ctypesutil import CLibrary, HANDLE
from can.exceptions import (
    CanInterfaceNotImplementedError,
    CanInitializationError,
    CanError,
)
from can.typechecking import CanFilters
from . import constants
from . import structures

__all__ = ["EcomBus", "get_ecom_devices"]

log = logging.getLogger("can.ecom")

# Load library.
_ecomlib = None
try:
    _ecomlib = CLibrary("ecommlib64.dll")
    if _ecomlib is None:
        raise CanInterfaceNotImplementedError("CLibrary not loaded.")
except Exception as e:
    log.error(f"Cannot load ECOMM library: {e}")

try:
    # BYTE GetErrorMessage(HANDLE DeviceHandle, ErrorMessage *ErrorMessage)
    _ecomlib.map_symbol(
        "GetErrorMessage", ctypes.c_byte, (HANDLE, structures.PErrorMessage)
    )

    # void GetFriendlyErrorMessage(BYTE ErrorCode, char *ErrorString,
    #   int ErrorStringSize)
    _ecomlib.map_symbol(
        "GetFriendlyErrorMessage",
        ctypes.c_int,
        (ctypes.c_byte, ctypes.POINTER(ctypes.c_char), ctypes.c_int),
    )

    # C-code function defs.
    # HANDLE CANOpen(ULONG SerialNumber, BYTE BaudRate, BYTE *ErrorResultCode)
    _ecomlib.map_symbol(
        "CANOpen",
        HANDLE,
        (ctypes.c_ulong, ctypes.c_byte, ctypes.POINTER(ctypes.c_byte)),
    )

    # HANDLE CANOpenFiltered(ULONG SerialNumber, BYTE BaudRate,
    #   DWORD AcceptanceCode, DWORD Acceptancemask, BYTE *ErrorReturnCode)
    _ecomlib.map_symbol(
        "CANOpenFiltered",
        HANDLE,
        (
            ctypes.c_ulong,
            ctypes.c_byte,
            structures.DWORD,
            structures.DWORD,
            ctypes.POINTER(ctypes.c_byte),
        ),
    )

    # NOTE: This is here for completeness but serial is not implemented.
    # HANDLE SerialOpen(USHORT SerialNumber, BYTE BaudRate, BYTE *ErrorReturnCode)

    # BYTE CloseDevice(HANDLE DeviceHandle)
    _ecomlib.map_symbol("CloseDevice", ctypes.c_byte, (HANDLE,))

    # BYTE CANSetupDevice(HANDLE DeviceHandle, BYTE SetupCommand,
    #   BYTE SetupProperty)
    _ecomlib.map_symbol(
        "CANSetupDevice", ctypes.c_byte, (HANDLE, ctypes.c_byte, ctypes.c_byte)
    )

    # BYTE CANTransmitMessage(HANDLE cdev, SFFMessage *message)
    _ecomlib.map_symbol(
        "CANTransmitMessage", ctypes.c_byte, (HANDLE, structures.PFFMessage)
    )

    # BYTE CANTransmitMessageEx(HANDLE cdev, EFFMessage *message)
    _ecomlib.map_symbol(
        "CANTransmitMessageEx", ctypes.c_byte, (HANDLE, structures.PFFMessage)
    )

    # BYTE CANReceiveMessageEx(HANDLE cdev, EFFMessage *message)
    _ecomlib.map_symbol(
        "CANReceiveMessageEx", ctypes.c_byte, (HANDLE, structures.PFFMessage)
    )

    # BYTE CANReceiveMessage(HANDLE cdev, SFFMessage *message)
    _ecomlib.map_symbol(
        "CANReceiveMessage", ctypes.c_byte, (HANDLE, structures.PFFMessage)
    )

    # NOTE: This is here for completeness but serial is not implemented.
    # BYTE SerialWrite(HANDLE DeviceHandle, BYTE *DataBuffer, LONG *Length)

    # NOTE: This is here for completeness but serial is not implemented.
    # BYTE SerialRead(HANDLE DeviceHandle, BYTE *DataBuffer, LONG *BufferLength)

    # DEV_SEARCH_HANDLE StartDeviceSearch(BYTE Flag)
    _ecomlib.map_symbol(
        "StartDeviceSearch", structures.DEV_SEARCH_HANDLE, (ctypes.c_byte,)
    )

    # BYTE CloseDeviceSearch(DEV_SEARCH_HANDLE SearchHandle)
    _ecomlib.map_symbol(
        "CloseDeviceSearch", ctypes.c_byte, (structures.DEV_SEARCH_HANDLE,)
    )

    # BYTE FindNextDevice(DEV_SEARCH_HANDLE SearchHandle, DeviceInfo *deviceInfo)
    _ecomlib.map_symbol(
        "FindNextDevice",
        ctypes.c_byte,
        (structures.DEV_SEARCH_HANDLE, structures.PDeviceInfo),
    )

    # BYTE GetDeviceInfo(HANDLE DeviceHandle, DeviceInfo *deviceInfo);
    _ecomlib.map_symbol(
        "GetDeviceInfo", ctypes.c_byte, (HANDLE, structures.PDeviceInfo)
    )

    # TODO : Implement pMessageCallback typedef to use.
    # BYTE SetCallbackFunction(HANDLE DeviceHandle,
    #   pMessageHandler *ReceiveCallback, void *UserData)

    # int GetQueueSize(HANDLE DeviceHandle, BYTE Flag)
    _ecomlib.map_symbol("GetQueueSize", ctypes.c_int, (HANDLE, ctypes.c_byte))
except Exception as e:
    log.error(f"Cannot initialize ECOMM library: {e}")


class EcomBus(BusABC):

    BITRATES = {
        125000: constants.CAN_BAUD_125K,
        250000: constants.CAN_BAUD_250K,
        500000: constants.CAN_BAUD_500K,
        1000000: constants.CAN_BAUD_1MB,
    }

    def __init__(self, channel=None, can_filters=None, **kwargs):
        """Construct and open a CAN bus instance of the specified type.

        Subclasses should call though this method with all given parameters
        as it handles generic tasks like applying filters.

        .. note:
            These devices only have one channel so argument is not used.

        :param list can_filters:
            See :meth:`~can.BusABC.set_filters` for details.

        :param dict kwargs:
            Any backend dependent configurations are passed in this dictionary
        """
        # Initial values.

        self._dev_hdl = None
        self._can_filters = can_filters
        # Call to super.
        super().__init__(channel=None, can_filters=self._can_filters, **kwargs)

        if _ecomlib is None:
            raise CanInterfaceNotImplementedError(
                "The ECOM library has not been initialized."
            )

        # Configuration options:
        serl_no = kwargs.get("serl_no", None)
        bitrate = kwargs.get("bitrate", 500000)
        self._bitrate = bitrate
        self._synchronous = kwargs.get("synchronous", False)
        if bitrate not in self.BITRATES:
            raise ValueError(f"Unsupported bitrate: {bitrate}")
        else:
            bitrate = self.BITRATES.get(bitrate)
        self._receive_own_messages = kwargs.get("receive_own_messages", False)

        # Get device serial number for present device.
        devices = get_ecom_devices()
        if serl_no not in devices:
            if serl_no is None:
                self._serl_no = devices[0]
            else:
                raise CanInitializationError(
                    f"Device with serial number '{serl_no}' not found."
                )
        else:
            self._serl_no = serl_no

        # Open device.
        try:
            err = ctypes.c_byte()
            if self._can_filters is None:
                # No filter.
                self._dev_hdl = _ecomlib.CANOpen(
                    self._serl_no, bitrate, ctypes.byref(err)
                )
            else:
                self._dev_hdl = _ecomlib.CANOpenFiltered(
                    self._serl_no,
                    bitrate,
                    self._can_filters["can_id"],
                    self._can_filters["can_mask"],
                    ctypes.byref(err),
                )
        except Exception as e:
            raise CanInitializationError(f"Could not open device: {e}")

        # Configure the device.
        # Defaults to asynchronous transmits (i.e., non-blocking).
        # python-can will perform SW blocking as defined in the interface.
        # If synchronous here, it will be blocked by HW; we want to leverage the
        # built-in buffer to be able to quickly respond.
        if self._synchronous:
            setup_args = (
                self._dev_hdl,
                constants.CAN_CMD_TRANSMIT,
                constants.CAN_PROPERTY_SYNC,
            )
        else:
            setup_args = (
                self._dev_hdl,
                constants.CAN_CMD_TRANSMIT,
                constants.CAN_PROPERTY_ASYNC,
            )
        _ecomlib.CANSetupDevice(*setup_args)

        self._tick_resl = constants.TIMESTAMP_RESL
        # Struct for receive messages.
        self._msg = structures.FFMessage()
        # Get max TX buffer.
        self._max_tx_buf = _ecomlib.GetQueueSize(
            self._dev_hdl, constants.CAN_GET_MAX_TX_SIZE
        )

    def send(self, msg: Message, timeout: Optional[float] = None) -> None:
        """Transmit a message to the CAN bus.

        Override this method to enable the transmit path.

        :param can.Message msg: A message object.

        :type timeout: float or None
        :param timeout:
            If > 0, wait up to this many seconds for message to be ACK'ed or
            for transmit queue to be ready depending on driver implementation.
            If timeout is exceeded, an exception will be raised.
            Might not be supported by all interfaces.
            None blocks indefinitely.

        :raises can.CanError:
            if the message could not be sent
        """

        if not isinstance(msg, Message):
            raise TypeError("'msg' must of type 'Message'.")

        # Prepare any message options.
        options = 0
        if msg.is_remote_frame:
            options |= 1 << 6
        if self._receive_own_messages:
            options |= 1 << 4
        # TODO : account for dlc

        # If the length of the message is not 8 bytes, append 0x00s until length is 8
        # Ultimately, any appended bytes beyond specified dlc will not be transmitted
        # anyway
        if len(msg.data) < 8:
            append_bytes = 8 - len(msg.data)
            for i in range(0, append_bytes):
                msg.data.append(0x00)

        data = (ctypes.c_byte * len(msg.data)).from_buffer(msg.data)

        # Begin tryign to transmit with consideration for the timeout.
        if timeout is None or timeout < 0:
            timeout = -1
        t0 = perf_counter()
        # This performs 'blocking' up until the timeout by checking if the
        # transmit buffer is full.
        # If we are synchronous the HW will block.
        while True and not self._synchronous:
            # While we want to ensure transmit and buffer is full.
            if (
                _ecomlib.GetQueueSize(self._dev_hdl, constants.CAN_GET_TX_SIZE)
                < self._max_tx_buf
            ):
                # Room in buffer; continue to transmit.
                break
            if (perf_counter() - t0) >= timeout != -1:
                # Timeout has expired and is not -1 (infinite).
                break

        message = structures.FFMessage()
        if msg.is_extended_id:
            # 29-bit
            message.EFFMessage.ID = msg.arbitration_id
            message.EFFMessage.Data = data
            message.EFFMessage.DataLength = msg.dlc
            message.EFFMessage.Options = options
            message.EFFMessage.TimeStamp = 0  # No meaning with TX.
            _ecomlib.CANTransmitMessageEx(self._dev_hdl, ctypes.byref(message))
        else:
            # 11-bit
            message.SFFMessage.IDH = msg.arbitration_id >> 8
            message.SFFMessage.IDL = msg.arbitration_id & 0xFF
            message.SFFMessage.Data = data
            message.SFFMessage.DataLength = msg.dlc
            message.SFFMessage.Options = options
            message.SFFMessage.TimeStamp = 0  # No meaning with TX.
            _ecomlib.CANTransmitMessage(self._dev_hdl, ctypes.byref(message))

    def _recv_std(self) -> Optional[Message]:
        msg = self._msg.SFFMessage
        size = _ecomlib.GetQueueSize(self._dev_hdl, constants.CAN_GET_SFF_SIZE)
        if size > 0:
            _ecomlib.CANReceiveMessage(self._dev_hdl, ctypes.byref(self._msg))
            rx_msg = Message(
                timestamp=msg.TimeStamp * self._tick_resl,
                is_remote_frame=bool(msg.Options & 0x40),
                is_extended_id=False,
                arbitration_id=(msg.IDH << 8) | msg.IDL,
                dlc=msg.DataLength,
                data=msg.Data,
                channel=None,
            )
        else:
            rx_msg = None
        return rx_msg

    def _recv_extended(self) -> Optional[Message]:
        msg = self._msg.EFFMessage
        size = _ecomlib.GetQueueSize(self._dev_hdl, constants.CAN_GET_EFF_SIZE)
        if size > 0:
            _ecomlib.CANReceiveMessageEx(self._dev_hdl, ctypes.byref(self._msg))
            rx_msg = Message(
                timestamp=msg.TimeStamp * self._tick_resl,
                is_remote_frame=bool(msg.Options & 0x40),
                is_extended_id=True,
                arbitration_id=msg.ID,
                dlc=msg.DataLength,
                data=msg.Data,
                channel=None,
            )
        else:
            rx_msg = None
        return rx_msg

    def _recv_internal(
        self, timeout: Optional[float]
    ) -> Tuple[Optional[Message], bool]:
        """
        Read a message from the bus and tell whether it was filtered.
        This methods may be called by :meth:`~can.BusABC.recv`
        to read a message multiple times if the filters set by
        :meth:`~can.BusABC.set_filters` do not match and the call has
        not yet timed out.

        New implementations should always override this method instead of
        :meth:`~can.BusABC.recv`, to be able to take advantage of the
        software based filtering provided by :meth:`~can.BusABC.recv`
        as a fallback. This method should never be called directly.

        .. note::

            This method is not an `@abstractmethod` (for now) to allow older
            external implementations to continue using their existing
            :meth:`~can.BusABC.recv` implementation.

        .. note::

            The second return value (whether filtering was already done) may
            change over time for some interfaces, like for example in the
            Kvaser interface. Thus it cannot be simplified to a constant value.

        :param float timeout: seconds to wait for a message,
                              see :meth:`~can.BusABC.send`

        :rtype: tuple[can.Message, bool] or tuple[None, bool]
        :return:
            1.  a message that was read or None on timeout
            2.  a bool that is True if message filtering has already
                been done and else False

        :raises can.CanError:
            if an error occurred while reading
        :raises NotImplementedError:
            if the bus provides it's own :meth:`~can.BusABC.recv`
            implementation (legacy implementation)

        """

        if timeout is None or timeout < 0:
            timeout = -1
        t0 = perf_counter()
        while True:
            rx_msg = self._recv_std()
            if rx_msg is not None:
                # Standard 11-bit message found.
                break
            rx_msg = self._recv_extended()
            if rx_msg is not None:
                # Extended 29-bit message found.
                break
            if (perf_counter() - t0) >= timeout != -1:
                # Timeout has expired and is not -1 (infinite).
                break
        return rx_msg, True

    def shutdown(self) -> None:
        _ecomlib.CloseDevice(self._dev_hdl)

    def _apply_filters(self, filters: Optional[CanFilters]) -> None:
        if self._dev_hdl is None:
            if filters is not None:
                # NOTES for SJA1000 CAN Transceiver:
                # CAN transceiver datasheet:
                #   https://www.nxp.com/docs/en/data-sheet/SJA1000.pdf
                # Standard:
                #   Complete identifier including RTR bit and first two data
                #   bytes are used for acceptance filtering.
                # Extended:
                #   Complete identifier including RTR bit are used for
                #   acceptance filtering.

                # Comma separated filters can be specified for the given
                # CAN interface: <can_id>:<can_mask> (matches when
                # <received_can_id> & mask == can_id & mask)
                # <can_id>~<can_mask> (matches when <received_can_id> &
                # mask != can_id & mask)
                self._acceptance_mask = filters["can_mask"]
                self._acceptance_code = filters["can_id"]
                try:
                    _extended_code = filters["extended"]
                except:
                    _extended_code = False

                # If the acceptance code is an 11-bit ID. Shift it to the MSB
                # of a 29-bit ID for CANOpenFiltered func
                if _extended_code == False:
                    self._can_filters["can_id"] = self._can_filters["can_id"] << 18
                # raise NotImplementedError("todo: implement filtering")
        else:
            raise CanError("Filter can only be set before connecting.")


def get_ecom_devices() -> List[int]:
    serl_nos = list()
    search_hndl = _ecomlib.StartDeviceSearch(constants.FIND_ALL)
    try:
        dev_info = structures.DeviceInfo()
        # Search through the devices until the one with the serial number is
        # found otherwise return any of them that aren't open.
        while (
            _ecomlib.FindNextDevice(search_hndl, ctypes.byref(dev_info))
            == constants.ECI_NO_ERROR
        ):
            serl_nos.append(dev_info.SerialNumber)
    finally:
        # Close search.
        _ecomlib.CloseDeviceSearch(search_hndl)
    return serl_nos

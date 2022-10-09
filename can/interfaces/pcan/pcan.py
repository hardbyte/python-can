"""
Enable basic CAN over a PCAN USB device.
"""

import logging
import time
from datetime import datetime
import platform

from typing import Optional

from packaging import version

from ...message import Message
from ...bus import BusABC, BusState
from ...util import len2dlc, dlc2len
from ...exceptions import CanError, CanOperationError, CanInitializationError


from .basic import (
    PCAN_BITRATES,
    PCAN_FD_PARAMETER_LIST,
    PCAN_CHANNEL_NAMES,
    PCAN_NONEBUS,
    PCAN_BAUD_500K,
    PCAN_TYPE_ISA,
    PCANBasic,
    PCAN_ERROR_OK,
    PCAN_ALLOW_ERROR_FRAMES,
    PCAN_PARAMETER_ON,
    PCAN_RECEIVE_EVENT,
    PCAN_API_VERSION,
    PCAN_DEVICE_NUMBER,
    PCAN_ERROR_QRCVEMPTY,
    PCAN_ERROR_BUSLIGHT,
    PCAN_ERROR_BUSHEAVY,
    PCAN_MESSAGE_EXTENDED,
    PCAN_MESSAGE_RTR,
    PCAN_MESSAGE_FD,
    PCAN_MESSAGE_BRS,
    PCAN_MESSAGE_ESI,
    PCAN_MESSAGE_ERRFRAME,
    PCAN_MESSAGE_STANDARD,
    TPCANMsgFD,
    TPCANMsg,
    PCAN_CHANNEL_IDENTIFYING,
    PCAN_LISTEN_ONLY,
    PCAN_PARAMETER_OFF,
    TPCANHandle,
    PCAN_PCIBUS1,
    PCAN_USBBUS1,
    PCAN_PCCBUS1,
    PCAN_LANBUS1,
    PCAN_CHANNEL_CONDITION,
    PCAN_CHANNEL_AVAILABLE,
    PCAN_CHANNEL_FEATURES,
    FEATURE_FD_CAPABLE,
    PCAN_DICT_STATUS,
    PCAN_BUSOFF_AUTORESET,
)


# Set up logging
log = logging.getLogger("can.pcan")

MIN_PCAN_API_VERSION = version.parse("4.2.0")


try:
    # use the "uptime" library if available
    import uptime

    # boottime() and fromtimestamp() are timezone offset, so the difference is not.
    if uptime.boottime() is None:
        boottimeEpoch = 0
    else:
        boottimeEpoch = (uptime.boottime() - datetime.fromtimestamp(0)).total_seconds()
except ImportError as error:
    log.warning(
        "uptime library not available, timestamps are relative to boot time and not to Epoch UTC",
        exc_info=True,
    )
    boottimeEpoch = 0

try:
    # Try builtin Python 3 Windows API
    from _overlapped import CreateEvent
    from _winapi import WaitForSingleObject, WAIT_OBJECT_0, INFINITE

    HAS_EVENTS = True
except ImportError:
    try:
        # Try pywin32 package
        from win32event import CreateEvent
        from win32event import WaitForSingleObject, WAIT_OBJECT_0, INFINITE

        HAS_EVENTS = True
    except ImportError:
        # Use polling instead
        HAS_EVENTS = False


class PcanBus(BusABC):
    def __init__(
        self,
        channel="PCAN_USBBUS1",
        device_id=None,
        state=BusState.ACTIVE,
        bitrate=500000,
        *args,
        **kwargs,
    ):
        """A PCAN USB interface to CAN.

        On top of the usual :class:`~can.Bus` methods provided,
        the PCAN interface includes the :meth:`flash`
        and :meth:`status` methods.

        :param str channel:
            The can interface name. An example would be 'PCAN_USBBUS1'.
            Alternatively the value can be an int with the numerical value.
            Default is 'PCAN_USBBUS1'

        :param int device_id:
            Select the PCAN interface based on its ID. The device ID is a 8/32bit
            value that can be configured for each PCAN device. If you set the
            device_id parameter, it takes precedence over the channel parameter.
            The constructor searches all connected interfaces and initializes the
            first one that matches the parameter value. If no device is found,
            an exception is raised.

        :param can.bus.BusState state:
            BusState of the channel.
            Default is ACTIVE

        :param int bitrate:
            Bitrate of channel in bit/s.
            Default is 500 kbit/s.
            Ignored if using CanFD.

        :param bool fd:
            Should the Bus be initialized in CAN-FD mode.

        :param int f_clock:
            Clock rate in Hz.
            Any of the following:
            20000000, 24000000, 30000000, 40000000, 60000000, 80000000.
            Ignored if not using CAN-FD.
            Pass either f_clock or f_clock_mhz.

        :param int f_clock_mhz:
            Clock rate in MHz.
            Any of the following:
            20, 24, 30, 40, 60, 80.
            Ignored if not using CAN-FD.
            Pass either f_clock or f_clock_mhz.

        :param int nom_brp:
            Clock prescaler for nominal time quantum.
            In the range (1..1024)
            Ignored if not using CAN-FD.

        :param int nom_tseg1:
            Time segment 1 for nominal bit rate,
            that is, the number of quanta from (but not including)
            the Sync Segment to the sampling point.
            In the range (1..256).
            Ignored if not using CAN-FD.

        :param int nom_tseg2:
            Time segment 2 for nominal bit rate,
            that is, the number of quanta from the sampling
            point to the end of the bit.
            In the range (1..128).
            Ignored if not using CAN-FD.

        :param int nom_sjw:
            Synchronization Jump Width for nominal bit rate.
            Decides the maximum number of time quanta
            that the controller can resynchronize every bit.
            In the range (1..128).
            Ignored if not using CAN-FD.

        :param int data_brp:
            Clock prescaler for fast data time quantum.
            In the range (1..1024)
            Ignored if not using CAN-FD.

        :param int data_tseg1:
            Time segment 1 for fast data bit rate,
            that is, the number of quanta from (but not including)
            the Sync Segment to the sampling point.
            In the range (1..32).
            Ignored if not using CAN-FD.

        :param int data_tseg2:
            Time segment 2 for fast data bit rate,
            that is, the number of quanta from the sampling
            point to the end of the bit.
            In the range (1..16).
            Ignored if not using CAN-FD.

        :param int data_sjw:
            Synchronization Jump Width for fast data bit rate.
            Decides the maximum number of time quanta
            that the controller can resynchronize every bit.
            In the range (1..16).
            Ignored if not using CAN-FD.

        :param bool auto_reset:
            Enable automatic recovery in bus off scenario.
            Resetting the driver takes ~500ms during which
            it will not be responsive.
        """
        self.m_objPCANBasic = PCANBasic()

        if device_id is not None:
            channel = self._find_channel_by_dev_id(device_id)

            if channel is None:
                err_msg = "Cannot find a channel with ID {:08x}".format(device_id)
                raise ValueError(err_msg)

        self.channel_info = str(channel)
        self.fd = kwargs.get("fd", False)
        pcan_bitrate = PCAN_BITRATES.get(bitrate, PCAN_BAUD_500K)

        hwtype = PCAN_TYPE_ISA
        ioport = 0x02A0
        interrupt = 11

        if not isinstance(channel, int):
            channel = PCAN_CHANNEL_NAMES[channel]

        self.m_PcanHandle = channel

        self.check_api_version()

        if state is BusState.ACTIVE or state is BusState.PASSIVE:
            self.state = state
        else:
            raise ValueError("BusState must be Active or Passive")

        if self.fd:
            f_clock_val = kwargs.get("f_clock", None)
            if f_clock_val is None:
                f_clock = "{}={}".format("f_clock_mhz", kwargs.get("f_clock_mhz", None))
            else:
                f_clock = "{}={}".format("f_clock", kwargs.get("f_clock", None))

            fd_parameters_values = [f_clock] + [
                "{}={}".format(key, kwargs.get(key, None))
                for key in PCAN_FD_PARAMETER_LIST
                if kwargs.get(key, None) is not None
            ]

            self.fd_bitrate = " ,".join(fd_parameters_values).encode("ascii")

            result = self.m_objPCANBasic.InitializeFD(
                self.m_PcanHandle, self.fd_bitrate
            )
        else:
            result = self.m_objPCANBasic.Initialize(
                self.m_PcanHandle, pcan_bitrate, hwtype, ioport, interrupt
            )

        if result != PCAN_ERROR_OK:
            raise PcanCanInitializationError(self._get_formatted_error(result))

        result = self.m_objPCANBasic.SetValue(
            self.m_PcanHandle, PCAN_ALLOW_ERROR_FRAMES, PCAN_PARAMETER_ON
        )

        if result != PCAN_ERROR_OK:
            if platform.system() != "Darwin":
                raise PcanCanInitializationError(self._get_formatted_error(result))
            else:
                # TODO Remove Filter when MACCan actually supports it:
                #  https://github.com/mac-can/PCBUSB-Library/
                log.debug(
                    "Ignoring error. PCAN_ALLOW_ERROR_FRAMES is still unsupported by OSX Library PCANUSB v0.10"
                )

        if kwargs.get("auto_reset", False):
            result = self.m_objPCANBasic.SetValue(
                self.m_PcanHandle, PCAN_BUSOFF_AUTORESET, PCAN_PARAMETER_ON
            )

            if result != PCAN_ERROR_OK:
                raise PcanCanInitializationError(self._get_formatted_error(result))

        if HAS_EVENTS:
            self._recv_event = CreateEvent(None, 0, 0, None)
            result = self.m_objPCANBasic.SetValue(
                self.m_PcanHandle, PCAN_RECEIVE_EVENT, self._recv_event
            )
            if result != PCAN_ERROR_OK:
                raise PcanCanInitializationError(self._get_formatted_error(result))

        super().__init__(channel=channel, state=state, bitrate=bitrate, *args, **kwargs)

    def _find_channel_by_dev_id(self, device_id):
        """
        Iterate over all possible channels to find a channel that matches the device
        ID. This method is somewhat brute force, but the Basic API only offers a
        suitable API call since V4.4.0.

        :param device_id: The device_id for which to search for
        :return: The name of a PCAN channel that matches the device ID, or None if
            no channel can be found.
        """
        for ch_name, ch_handle in PCAN_CHANNEL_NAMES.items():
            err, cur_dev_id = self.m_objPCANBasic.GetValue(
                ch_handle, PCAN_DEVICE_NUMBER
            )
            if err != PCAN_ERROR_OK:
                continue

            if cur_dev_id == device_id:
                return ch_name

        return None

    def _get_formatted_error(self, error):
        """
        Gets the text using the GetErrorText API function.
        If the function call succeeds, the translated error is returned. If it fails,
        a text describing the current error is returned. Multiple errors may
        be present in which case their individual messages are included in the
        return string, one line per error.
        """

        def bits(n):
            """
            Iterate over all the set bits in `n`, returning the masked bits at
            the set indices
            """
            while n:
                # Create a mask to mask the lowest set bit in n
                mask = ~n + 1
                masked_value = n & mask
                yield masked_value
                # Toggle the lowest set bit
                n ^= masked_value

        stsReturn = self.m_objPCANBasic.GetErrorText(error, 0x9)
        if stsReturn[0] != PCAN_ERROR_OK:
            strings = []

            for b in bits(error):
                stsReturn = self.m_objPCANBasic.GetErrorText(b, 0x9)
                if stsReturn[0] != PCAN_ERROR_OK:
                    text = "An error occurred. Error-code's text ({0:X}h) couldn't be retrieved".format(
                        error
                    )
                else:
                    text = stsReturn[1].decode("utf-8", errors="replace")

                strings.append(text)

            complete_text = "\n".join(strings)
        else:
            complete_text = stsReturn[1].decode("utf-8", errors="replace")

        return complete_text

    def get_api_version(self):
        error, value = self.m_objPCANBasic.GetValue(PCAN_NONEBUS, PCAN_API_VERSION)
        if error != PCAN_ERROR_OK:
            raise CanInitializationError(f"Failed to read pcan basic api version")

        return version.parse(value.decode("ascii"))

    def check_api_version(self):
        apv = self.get_api_version()
        if apv < MIN_PCAN_API_VERSION:
            log.warning(
                f"Minimum version of pcan api is {MIN_PCAN_API_VERSION}."
                f" Installed version is {apv}. Consider upgrade of pcan basic package"
            )

    def status(self):
        """
        Query the PCAN bus status.

        :rtype: int
        :return: The status code. See values in **basic.PCAN_ERROR_**
        """
        return self.m_objPCANBasic.GetStatus(self.m_PcanHandle)

    def status_is_ok(self):
        """
        Convenience method to check that the bus status is OK
        """
        status = self.status()
        return status == PCAN_ERROR_OK

    def reset(self):
        """
        Command the PCAN driver to reset the bus after an error.
        """
        status = self.m_objPCANBasic.Reset(self.m_PcanHandle)
        return status == PCAN_ERROR_OK

    def get_device_number(self):
        """
        Return the PCAN device number.

        :rtype: int
        :return: PCAN device number
        """
        error, value = self.m_objPCANBasic.GetValue(
            self.m_PcanHandle, PCAN_DEVICE_NUMBER
        )
        if error != PCAN_ERROR_OK:
            return None
        return value

    def set_device_number(self, device_number):
        """
        Set the PCAN device number.

        :param device_number: new PCAN device number
        :rtype: bool
        :return: True if device number set successfully
        """
        try:
            if (
                self.m_objPCANBasic.SetValue(
                    self.m_PcanHandle, PCAN_DEVICE_NUMBER, int(device_number)
                )
                != PCAN_ERROR_OK
            ):
                raise ValueError()
        except ValueError:
            log.error("Invalid value '%s' for device number.", device_number)
            return False
        return True

    def _recv_internal(self, timeout):

        if HAS_EVENTS:
            # We will utilize events for the timeout handling
            timeout_ms = int(timeout * 1000) if timeout is not None else INFINITE
        elif timeout is not None:
            # Calculate max time
            end_time = time.perf_counter() + timeout

        # log.debug("Trying to read a msg")

        result = None
        while result is None:
            if self.fd:
                result = self.m_objPCANBasic.ReadFD(self.m_PcanHandle)
            else:
                result = self.m_objPCANBasic.Read(self.m_PcanHandle)
            if result[0] == PCAN_ERROR_QRCVEMPTY:
                if HAS_EVENTS:
                    result = None
                    val = WaitForSingleObject(self._recv_event, timeout_ms)
                    if val != WAIT_OBJECT_0:
                        return None, False
                elif timeout is not None and time.perf_counter() >= end_time:
                    return None, False
                else:
                    result = None
                    time.sleep(0.001)
            elif result[0] & (PCAN_ERROR_BUSLIGHT | PCAN_ERROR_BUSHEAVY):
                log.warning(self._get_formatted_error(result[0]))
                return None, False
            elif result[0] != PCAN_ERROR_OK:
                raise PcanCanOperationError(self._get_formatted_error(result[0]))

        theMsg = result[1]
        itsTimeStamp = result[2]

        # log.debug("Received a message")

        is_extended_id = (
            theMsg.MSGTYPE & PCAN_MESSAGE_EXTENDED.value
        ) == PCAN_MESSAGE_EXTENDED.value
        is_remote_frame = (
            theMsg.MSGTYPE & PCAN_MESSAGE_RTR.value
        ) == PCAN_MESSAGE_RTR.value
        is_fd = (theMsg.MSGTYPE & PCAN_MESSAGE_FD.value) == PCAN_MESSAGE_FD.value
        bitrate_switch = (
            theMsg.MSGTYPE & PCAN_MESSAGE_BRS.value
        ) == PCAN_MESSAGE_BRS.value
        error_state_indicator = (
            theMsg.MSGTYPE & PCAN_MESSAGE_ESI.value
        ) == PCAN_MESSAGE_ESI.value
        is_error_frame = (
            theMsg.MSGTYPE & PCAN_MESSAGE_ERRFRAME.value
        ) == PCAN_MESSAGE_ERRFRAME.value

        if self.fd:
            dlc = dlc2len(theMsg.DLC)
            timestamp = boottimeEpoch + (itsTimeStamp.value / (1000.0 * 1000.0))
        else:
            dlc = theMsg.LEN
            timestamp = boottimeEpoch + (
                (
                    itsTimeStamp.micros
                    + 1000 * itsTimeStamp.millis
                    + 0x100000000 * 1000 * itsTimeStamp.millis_overflow
                )
                / (1000.0 * 1000.0)
            )

        rx_msg = Message(
            timestamp=timestamp,
            arbitration_id=theMsg.ID,
            is_extended_id=is_extended_id,
            is_remote_frame=is_remote_frame,
            is_error_frame=is_error_frame,
            dlc=dlc,
            data=theMsg.DATA[:dlc],
            is_fd=is_fd,
            bitrate_switch=bitrate_switch,
            error_state_indicator=error_state_indicator,
        )

        return rx_msg, False

    def send(self, msg, timeout=None):
        msgType = (
            PCAN_MESSAGE_EXTENDED.value
            if msg.is_extended_id
            else PCAN_MESSAGE_STANDARD.value
        )
        if msg.is_remote_frame:
            msgType |= PCAN_MESSAGE_RTR.value
        if msg.is_error_frame:
            msgType |= PCAN_MESSAGE_ERRFRAME.value
        if msg.is_fd:
            msgType |= PCAN_MESSAGE_FD.value
        if msg.bitrate_switch:
            msgType |= PCAN_MESSAGE_BRS.value
        if msg.error_state_indicator:
            msgType |= PCAN_MESSAGE_ESI.value

        if self.fd:
            # create a TPCANMsg message structure
            CANMsg = TPCANMsgFD()

            # configure the message. ID, Length of data, message type and data
            CANMsg.ID = msg.arbitration_id
            CANMsg.DLC = len2dlc(msg.dlc)
            CANMsg.MSGTYPE = msgType

            # copy data
            for i in range(msg.dlc):
                CANMsg.DATA[i] = msg.data[i]

            log.debug("Data: %s", msg.data)
            log.debug("Type: %s", type(msg.data))

            result = self.m_objPCANBasic.WriteFD(self.m_PcanHandle, CANMsg)

        else:
            # create a TPCANMsg message structure
            CANMsg = TPCANMsg()

            # configure the message. ID, Length of data, message type and data
            CANMsg.ID = msg.arbitration_id
            CANMsg.LEN = msg.dlc
            CANMsg.MSGTYPE = msgType

            # if a remote frame will be sent, data bytes are not important.
            if not msg.is_remote_frame:
                # copy data
                for i in range(CANMsg.LEN):
                    CANMsg.DATA[i] = msg.data[i]

            log.debug("Data: %s", msg.data)
            log.debug("Type: %s", type(msg.data))

            result = self.m_objPCANBasic.Write(self.m_PcanHandle, CANMsg)

        if result != PCAN_ERROR_OK:
            raise PcanCanOperationError(
                "Failed to send: " + self._get_formatted_error(result)
            )

    def flash(self, flash):
        """
        Turn on or off flashing of the device's LED for physical
        identification purposes.
        """
        self.m_objPCANBasic.SetValue(
            self.m_PcanHandle, PCAN_CHANNEL_IDENTIFYING, bool(flash)
        )

    def shutdown(self):
        super().shutdown()
        self.m_objPCANBasic.Uninitialize(self.m_PcanHandle)

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, new_state):
        # declare here, which is called by __init__()
        self._state = new_state  # pylint: disable=attribute-defined-outside-init

        if new_state is BusState.ACTIVE:
            self.m_objPCANBasic.SetValue(
                self.m_PcanHandle, PCAN_LISTEN_ONLY, PCAN_PARAMETER_OFF
            )

        elif new_state is BusState.PASSIVE:
            # When this mode is set, the CAN controller does not take part on active events (eg. transmit CAN messages)
            # but stays in a passive mode (CAN monitor), in which it can analyse the traffic on the CAN bus used by a
            # PCAN channel. See also the Philips Data Sheet "SJA1000 Stand-alone CAN controller".
            self.m_objPCANBasic.SetValue(
                self.m_PcanHandle, PCAN_LISTEN_ONLY, PCAN_PARAMETER_ON
            )

    @staticmethod
    def _detect_available_configs():
        channels = []
        try:
            library_handle = PCANBasic()
        except OSError:
            return channels
        interfaces = []
        for i in range(16):
            interfaces.append(
                {
                    "id": TPCANHandle(PCAN_PCIBUS1.value + i),
                    "name": "PCAN_PCIBUS" + str(i + 1),
                }
            )
        for i in range(16):
            interfaces.append(
                {
                    "id": TPCANHandle(PCAN_USBBUS1.value + i),
                    "name": "PCAN_USBBUS" + str(i + 1),
                }
            )
        for i in range(2):
            interfaces.append(
                {
                    "id": TPCANHandle(PCAN_PCCBUS1.value + i),
                    "name": "PCAN_PCCBUS" + str(i + 1),
                }
            )
        for i in range(16):
            interfaces.append(
                {
                    "id": TPCANHandle(PCAN_LANBUS1.value + i),
                    "name": "PCAN_LANBUS" + str(i + 1),
                }
            )
        for i in interfaces:
            try:
                error, value = library_handle.GetValue(i["id"], PCAN_CHANNEL_CONDITION)
                if error != PCAN_ERROR_OK or value != PCAN_CHANNEL_AVAILABLE:
                    continue
                has_fd = False
                error, value = library_handle.GetValue(i["id"], PCAN_CHANNEL_FEATURES)
                if error == PCAN_ERROR_OK:
                    has_fd = bool(value & FEATURE_FD_CAPABLE)
                channels.append(
                    {"interface": "pcan", "channel": i["name"], "supports_fd": has_fd}
                )
            except AttributeError:  # Ignore if this fails for some interfaces
                pass
        return channels

    def status_string(self) -> Optional[str]:
        """
        Query the PCAN bus status.

        :return: The status description, if any was found.
        """
        try:
            return PCAN_DICT_STATUS[self.status()]
        except KeyError:
            return None


class PcanError(CanError):
    """A generic error on a PCAN bus."""


class PcanCanOperationError(CanOperationError, PcanError):
    """Like :class:`can.exceptions.CanOperationError`, but specific to Pcan."""


class PcanCanInitializationError(CanInitializationError, PcanError):
    """Like :class:`can.exceptions.CanInitializationError`, but specific to Pcan."""

"""
NI-XNET interface module.

Implementation references:
    NI-XNET Hardware and Software Manual: https://www.ni.com/pdf/manuals/372840h.pdf
    NI-XNET Python implementation: https://github.com/ni/nixnet-python

Authors: Javier Rubio Giménez <jvrr20@gmail.com>, Jose A. Escobar <joseleescobar@hotmail.com>
"""

import logging
import sys
import time
import struct

from can import BusABC, Message
from ..exceptions import CanInitializationError, CanOperationError


logger = logging.getLogger(__name__)

if sys.platform == "win32":
    try:
        from nixnet import (
            session,
            types,
            constants,
            errors,
            system,
            database,
            XnetError,
        )
    except ImportError as error:
        raise ImportError("NIXNET python module cannot be loaded") from error
else:
    raise NotImplementedError("NiXNET only supported on Win32 platforms")


class NiXNETcanBus(BusABC):
    """
    The CAN Bus implemented for the NI-XNET interface.
    """

    def __init__(
        self,
        channel,
        can_filters=None,
        bitrate=None,
        fd=False,
        fd_bitrate=None,
        brs=False,
        can_termination=False,
        log_errors=True,
        **kwargs,
    ):
        """
        :param str channel:
            Name of the object to open (e.g. 'CAN0')

        :param int bitrate:
            Bitrate in bits/s

        :param list can_filters:
            See :meth:`can.BusABC.set_filters`.

        :param bool log_errors:
            If True, communication errors will appear as CAN messages with
            ``is_error_frame`` set to True and ``arbitration_id`` will identify
            the error (default True)

        :raises can.exceptions.CanInitializationError:
            If starting communication fails
        """
        self._rx_queue = []
        self.channel = channel
        self.channel_info = "NI-XNET: " + channel

        # Set database for the initialization
        if not fd:
            database_name = ":memory:"
        else:
            if not brs:
                database_name = ":can_fd:"
            else:
                database_name = ":can_fd_brs:"

        try:

            # We need two sessions for this application, one to send frames and another to receive them

            self.__session_send = session.FrameOutStreamSession(
                channel, database_name=database_name
            )
            self.__session_receive = session.FrameInStreamSession(
                channel, database_name=database_name
            )

            # We stop the sessions to allow reconfiguration, as by default they autostart at creation
            self.__session_send.stop()
            self.__session_receive.stop()

            # See page 1017 of NI-XNET Hardware and Software Manual to set custom can configuration
            if bitrate:
                self.__session_send.intf.baud_rate = bitrate
                self.__session_receive.intf.baud_rate = bitrate

            if fd_bitrate:
                # See page 951 of NI-XNET Hardware and Software Manual to set custom can configuration
                self.__session_send.intf.can_fd_baud_rate = fd_bitrate
                self.__session_receive.intf.can_fd_baud_rate = fd_bitrate

            if can_termination:
                self.__session_send.intf.can_term = constants.CanTerm.ON
                self.__session_receive.intf.can_term = constants.CanTerm.ON

            self.__session_receive.queue_size = 512
            # Once that all the parameters have been restarted, we start the sessions
            self.__session_send.start()
            self.__session_receive.start()

        except errors.XnetError as error:
            raise CanInitializationError(
                f"{error.args[0]} ({error.error_type})", error.error_code
            ) from None

        self._is_filtered = False
        super(NiXNETcanBus, self).__init__(
            channel=channel,
            can_filters=can_filters,
            bitrate=bitrate,
            log_errors=log_errors,
            **kwargs,
        )

    def _recv_internal(self, timeout):
        try:
            if len(self._rx_queue) == 0:
                fr = self.__session_receive.frames.read(4, timeout=0)
                for f in fr:
                    self._rx_queue.append(f)
            can_frame = self._rx_queue.pop(0)

            # Timestamp should be converted from raw frame format(100ns increment from(12:00 a.m. January 1 1601 Coordinated
            # Universal Time (UTC)) to epoch time(number of seconds from January 1, 1970 (midnight UTC/GMT))
            msg = Message(
                timestamp=can_frame.timestamp / 10000000.0 - 11644473600,
                channel=self.channel,
                is_remote_frame=can_frame.type == constants.FrameType.CAN_REMOTE,
                is_error_frame=can_frame.type == constants.FrameType.CAN_BUS_ERROR,
                is_fd=(
                    can_frame.type == constants.FrameType.CANFD_DATA
                    or can_frame.type == constants.FrameType.CANFDBRS_DATA
                ),
                bitrate_switch=can_frame.type == constants.FrameType.CANFDBRS_DATA,
                is_extended_id=can_frame.identifier.extended,
                # Get identifier from CanIdentifier structure
                arbitration_id=can_frame.identifier.identifier,
                dlc=len(can_frame.payload),
                data=can_frame.payload,
            )

            return msg, self._filters is None
        except Exception:
            return None, self._filters is None

    def send(self, msg, timeout=None):
        """
        Send a message using NI-XNET.

        :param can.Message msg:
            Message to send

        :param float timeout:
            Max time to wait for the device to be ready in seconds, None if time is infinite

        :raises can.exceptions.CanOperationError:
            If writing to transmit buffer fails.
            It does not wait for message to be ACKed currently.
        """
        if timeout is None:
            timeout = constants.TIMEOUT_INFINITE

        if msg.is_remote_frame:
            type_message = constants.FrameType.CAN_REMOTE
        elif msg.is_error_frame:
            type_message = constants.FrameType.CAN_BUS_ERROR
        elif msg.is_fd:
            if msg.bitrate_switch:
                type_message = constants.FrameType.CANFDBRS_DATA
            else:
                type_message = constants.FrameType.CANFD_DATA
        else:
            type_message = constants.FrameType.CAN_DATA

        can_frame = types.CanFrame(
            types.CanIdentifier(msg.arbitration_id, msg.is_extended_id),
            type=type_message,
            payload=msg.data,
        )

        try:
            self.__session_send.frames.write([can_frame], timeout)
        except errors.XnetError as error:
            raise CanOperationError(
                f"{error.args[0]} ({error.error_type})", error.error_code
            ) from None

    def reset(self):
        """
        Resets network interface. Stops network interface, then resets the CAN
        chip to clear the CAN error counters (clear error passive state).
        Resetting includes clearing all entries from read and write queues.
        """
        self.__session_send.flush()
        self.__session_receive.flush()

        self.__session_send.stop()
        self.__session_receive.stop()

        self.__session_send.start()
        self.__session_receive.start()

    def shutdown(self):
        """Close object."""
        super().shutdown()
        self.__session_send.flush()
        self.__session_receive.flush()

        self.__session_send.stop()
        self.__session_receive.stop()

        self.__session_send.close()
        self.__session_receive.close()

    @staticmethod
    def _detect_available_configs():
        configs = []

        try:
            with system.System() as nixnet_system:
                for interface in nixnet_system.intf_refs_can:
                    cahnnel = str(interface)
                    logger.debug(
                        "Found channel index %d: %s", interface.port_num, cahnnel
                    )
                    configs.append(
                        {
                            "interface": "nixnet",
                            "channel": cahnnel,
                            "can_term_available": interface.can_term_cap
                            == constants.CanTermCap.YES,
                        }
                    )
        except XnetError as error:
            logger.debug("An error occured while searching for configs: %s", str(error))

        return configs

import socket
import struct
import logging
from time import sleep
from typing import Optional, Dict, Any, Tuple
from can import BitTiming, BusABC, Message, typechecking
from can.typechecking import CanFilters


class UsrCanetBus(BusABC):

    def __init__(self,
                 host: str = '127.0.0.1',
                 port: int = 20001,
                 can_filters: Optional[typechecking.CanFilters] = None,
                 reconnect=True,
                 reconnect_delay=2,
                 **kwargs: Dict[str, Any]):
        """

        :param host:
            IP adddress of USR-CANET200 Device in TCP Server mode.
        :param port:
            TCP port of the corresponding CANbus port on the device configured.
        :param can_filters:
            Passed in for super class' filter.
        """

        super().__init__(can_filters=can_filters, **kwargs, channel=0)

        self.reconnect = reconnect
        self.host = host
        self.port = port
        self.connected = False
        self.reconnect_delay = reconnect_delay

        # Create a socket and connect to host
        while not self.connected:
            try:
                self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.s.connect((host, port))
                self.connected = True
            except socket.error as e:
                self.connected = False
                logging.error(f"Could not connect: {e}. Retrying...")
                self.s.close()
                sleep(reconnect_delay)

    def send(self, msg: Message, timeout: Optional[float] = None) -> None:
        """Send a CAN message to the bus

        :param msg: message to send

        :param timeout: timeout (in seconds) to wait for expected ACK pack.
        If set to ``None`` (default) will wait indefinitely.

        """
        frame_information = 0x00
        frame_information |= (1 if msg.is_extended_id else 0) << 7      # First bit indicates if is extended id
        frame_information |= (1 if msg.is_remote_frame else 0) << 6     # Second bit indicates if is remote frame
        frame_information |= msg.dlc & 0x0F                             # Last 4 bits indicate the length of frame
        frame_information = bytearray([frame_information])

        frame_id = bytearray(4)
        struct.pack_into('>L', frame_id, 0, int(msg.arbitration_id))    # Next 4 bytes contain CAN ID

        frame_data = bytearray(8)
        frame_data[0:len(msg.data)] = msg.data                      # Following 8 bytes contain CAN data

        raw_message = frame_information + frame_id + frame_data         # Combine to make full message

        # Set timeout for sending
        if timeout is not None:
            self.s.settimeout(timeout)
        try:
            self.s.send(raw_message)
        except TimeoutError:
            # Timeout
            msg = None
            pass
        except socket.error as e:
            self.connected = False
            logging.error(f"Socket error: {e}")
            if self.reconnect:
                self.do_reconnect()
            else:
                msg = None
        finally:
            # Reset timeout
            if timeout is not None:
                self.s.settimeout(None)

        return (msg, False)

    def do_reconnect(self):
        while not self.connected:
            try:
                logging.error("Reconnecting...")
                self.s.close()
                self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.s.connect((self.host, self.port))
                self.connected = True
                logging.error("Reconnected.")
            except Exception as e:
                logging.error(f"Could not reconnect: {e}. Retrying...")
                sleep(self.reconnect_delay)

    def _recv_internal(self, timeout: Optional[float]) -> Tuple[Optional[Message], bool]:
        """Expect a message to receive from the socket
        :param timeout: timeout (in seconds) to wait for expected data to come in.
        If set to ``None`` (default) will wait indefinitely.

        """

        # Set timeout and receive data
        if timeout is not None:
            self.s.settimeout(timeout)

        flag_success = False
        while not flag_success:
            try:
                # The USR-CANET will always return 13 bytes per CAN packet
                # But sometimes will return TCP packets with 2 CAN packets sandwiched together
                # This will seperate the sandwich.
                data = self.s.recv(13)
                flag_success = True
            except TimeoutError:
                self.s.settimeout(None)
                return(None, False)
            except socket.error as e:
                self.connected = False
                logging.error(f"Socket error: {e}")
                if self.reconnect:
                    self.do_reconnect()
                else:
                    self.s.settimeout(None)
                    return(None, False)


        # Check received length
        if len(data) == 0:
            self.s.settimeout(None)
            return (None, False)

        # Decode CAN frame
        # CAN frame from USR-CANET200 looks like:
        #  --------------------- ------------------ --------------------
        # | frame_info (1 byte) | can_id (4 bytes) | can_data (8 bytes) |
        #  --------------------- ------------------ --------------------
        CAN_FRAME = struct.Struct('>BI8s')
        frame_info, can_id, can_data = CAN_FRAME.unpack_from(data)
        dlc = frame_info & 0x0F                 # Last 4 bits indicate data length
        is_extended_id = frame_info & 0x80      # First bit indicate if is extended ID
        is_remote_frame = frame_info & 0x40     # Second bit indicate if is remote frame
        can_data = can_data[:dlc]               # Trim message
        msg = Message(arbitration_id=can_id,
                          data=can_data, dlc=dlc,
                          is_extended_id=is_extended_id,
                          is_remote_frame=is_remote_frame)

        # Reset timeout
        if timeout is not None:
            self.s.settimeout(None)
        return (msg, False)

    def shutdown(self) -> None:
        """Close down the socket and release resources immediately."""

        super().shutdown()
        self.s.close()


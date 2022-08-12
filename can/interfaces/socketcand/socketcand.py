"""
Interface to socketcand
see https://github.com/linux-can/socketcand

Authors: Marvin Seiler, Gerrit Telkamp

Copyright (C) 2021  DOMOLOGIC GmbH
http://www.domologic.de
"""
import can
import socket
import select
import logging
import time
import traceback
from collections import deque

log = logging.getLogger(__name__)


def convert_ascii_message_to_can_message(ascii_msg: str) -> can.Message:
    if not ascii_msg.startswith("< frame ") or not ascii_msg.endswith(" >"):
        log.warning(f"Could not parse ascii message: {ascii_msg}")
        return None
    else:
        # frame_string = ascii_msg.removeprefix("< frame ").removesuffix(" >")
        frame_string = ascii_msg[8:-2]
        parts = frame_string.split(" ", 3)
        can_id, timestamp = int(parts[0], 16), float(parts[1])

        data = bytearray.fromhex(parts[2])
        can_dlc = len(data)
        can_message = can.Message(
            timestamp=timestamp, arbitration_id=can_id, data=data, dlc=can_dlc
        )
        return can_message


def convert_can_message_to_ascii_message(can_message: can.Message) -> str:
    # Note: socketcan bus adds extended flag, remote_frame_flag & error_flag to id
    # not sure if that is necessary here
    can_id = can_message.arbitration_id
    # Note: seems like we cannot add CANFD_BRS (bitrate_switch) and CANFD_ESI (error_state_indicator) flags
    data = can_message.data
    length = can_message.dlc
    bytes_string = " ".join("{:x}".format(x) for x in data[0:length])
    return f"< send {can_id:X} {length:X} {bytes_string} >"


def connect_to_server(s, host, port):
    timeout_ms = 10000
    now = time.time() * 1000
    end_time = now + timeout_ms
    while now < end_time:
        try:
            s.connect((host, port))
            return
        except Exception as e:
            log.warning(f"Failed to connect to server: {type(e)} Message: {e}")
            now = time.time() * 1000
    raise TimeoutError(
        f"connect_to_server: Failed to connect server for {timeout_ms} ms"
    )


class SocketCanDaemonBus(can.BusABC):
    def __init__(self, channel, host, port, can_filters=None, **kwargs):
        self.__host = host
        self.__port = port
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__message_buffer = deque()
        self.__receive_buffer = ""  # i know string is not the most efficient here
        connect_to_server(self.__socket, self.__host, self.__port)
        self._expect_msg("< hi >")

        log.info(
            f"SocketCanDaemonBus: connected with address {self.__socket.getsockname()}"
        )
        self._tcp_send(f"< open {channel} >")
        self._expect_msg("< ok >")
        self._tcp_send(f"< rawmode >")
        self._expect_msg("< ok >")
        super().__init__(channel=channel, can_filters=can_filters)

    def _recv_internal(self, timeout):
        if len(self.__message_buffer) != 0:
            can_message = self.__message_buffer.popleft()
            return can_message, False

        try:
            # get all sockets that are ready (can be a list with a single value
            # being self.socket or an empty list if self.socket is not ready)
            ready_receive_sockets, _, _ = select.select(
                [self.__socket], [], [], timeout
            )
        except OSError as exc:
            # something bad happened (e.g. the interface went down)
            log.error(f"Failed to receive: {exc}")
            raise can.CanError(f"Failed to receive: {exc}")

        try:
            if not ready_receive_sockets:
                # socket wasn't readable or timeout occurred
                log.debug("Socket not ready")
                return None, False

            ascii_msg = self.__socket.recv(1024).decode(
                "ascii"
            )  # may contain multiple messages
            self.__receive_buffer += ascii_msg
            log.debug(f"Received Ascii Message: {ascii_msg}")
            buffer_view = self.__receive_buffer
            chars_processed_successfully = 0
            while True:
                if len(buffer_view) == 0:
                    break

                start = buffer_view.find("<")
                if start == -1:
                    log.warning(
                        f"Bad data: No opening < found => discarding entire buffer '{buffer_view}'"
                    )
                    chars_processed_successfully = len(self.__receive_buffer)
                    break
                end = buffer_view.find(">")
                if end == -1:
                    log.warning("Got incomplete message => waiting for more data")
                    if len(buffer_view) > 200:
                        log.warning(
                            "Incomplete message exceeds 200 chars => Discarding"
                        )
                        chars_processed_successfully = len(self.__receive_buffer)
                    break
                chars_processed_successfully += end + 1
                single_message = buffer_view[start : end + 1]
                parsed_can_message = convert_ascii_message_to_can_message(
                    single_message
                )
                if parsed_can_message is None:
                    log.warning(f"Invalid Frame: {single_message}")
                else:
                    self.__message_buffer.append(parsed_can_message)
                buffer_view = buffer_view[end + 1 :]

            self.__receive_buffer = self.__receive_buffer[
                chars_processed_successfully + 1 :
            ]
            can_message = (
                None
                if len(self.__message_buffer) == 0
                else self.__message_buffer.popleft()
            )
            return can_message, False

        except Exception as exc:
            log.error(f"Failed to receive: {exc}  {traceback.format_exc()}")
            raise can.CanError(f"Failed to receive: {exc}  {traceback.format_exc()}")

    def _tcp_send(self, msg: str):
        log.debug(f"Sending TCP Message: '{msg}'")
        self.__socket.sendall(msg.encode("ascii"))

    def _expect_msg(self, msg):
        ascii_msg = self.__socket.recv(256).decode("ascii")
        if not ascii_msg == msg:
            raise can.CanError(f"{msg} message expected!")

    def send(self, msg, timeout=None):
        ascii_msg = convert_can_message_to_ascii_message(msg)
        self._tcp_send(ascii_msg)

    def shutdown(self):
        self.stop_all_periodic_tasks()
        self.__socket.close()

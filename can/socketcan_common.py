"""
Defines shared SocketCAN methods and constants.
"""

import logging
import struct
from typing import Tuple

import can.util

from .message import Message

# Generic socket constants
SO_TIMESTAMPNS = 35

CAN_ERR_FLAG = 0x20000000
CAN_RTR_FLAG = 0x40000000
CAN_EFF_FLAG = 0x80000000

# BCM opcodes
CAN_BCM_TX_SETUP = 1
CAN_BCM_TX_DELETE = 2
CAN_BCM_TX_READ = 3

# BCM flags
SETTIMER = 0x0001
STARTTIMER = 0x0002
TX_COUNTEVT = 0x0004
TX_ANNOUNCE = 0x0008
TX_CP_CAN_ID = 0x0010
RX_FILTER_ID = 0x0020
RX_CHECK_DLC = 0x0040
RX_NO_AUTOTIMER = 0x0080
RX_ANNOUNCE_RESUME = 0x0100
TX_RESET_MULTI_IDX = 0x0200
RX_RTR_FRAME = 0x0400
CAN_FD_FRAME = 0x0800

CAN_RAW = 1
CAN_BCM = 2

SOL_CAN_BASE = 100
SOL_CAN_RAW = SOL_CAN_BASE + CAN_RAW

CAN_RAW_FILTER = 1
CAN_RAW_ERR_FILTER = 2
CAN_RAW_LOOPBACK = 3
CAN_RAW_RECV_OWN_MSGS = 4
CAN_RAW_FD_FRAMES = 5

MSK_ARBID = 0x1FFFFFFF
MSK_FLAGS = 0xE0000000

PF_CAN = 29
SOCK_RAW = 3
SOCK_DGRAM = 2
AF_CAN = PF_CAN

SIOCGIFNAME = 0x8910
SIOCGIFINDEX = 0x8933
SIOCGSTAMP = 0x8906
EXTFLG = 0x0004

CANFD_BRS = 0x01  # bit rate switch (second bitrate for payload data)
CANFD_ESI = 0x02  # error state indicator of the transmitting node
CANFD_FDF = 0x04  # mark CAN FD for dual use of struct canfd_frame

# CAN payload length and DLC definitions according to ISO 11898-1
CAN_MAX_DLC = 8
CAN_MAX_RAW_DLC = 15
CAN_MAX_DLEN = 8

# CAN FD payload length and DLC definitions according to ISO 11898-7
CANFD_MAX_DLC = 15
CANFD_MAX_DLEN = 64

CANFD_MTU = 72

STD_ACCEPTANCE_MASK_ALL_BITS = 2**11 - 1
MAX_11_BIT_ID = STD_ACCEPTANCE_MASK_ALL_BITS

EXT_ACCEPTANCE_MASK_ALL_BITS = 2**29 - 1
MAX_29_BIT_ID = EXT_ACCEPTANCE_MASK_ALL_BITS

# struct module defines a binary packing format:
# https://docs.python.org/3/library/struct.html#struct-format-strings
# The 32bit can id is directly followed by the 8bit data link count
# The data field is aligned on an 8 byte boundary, hence we add padding
# which aligns the data field to an 8 byte boundary.

# host-endian for communication with kernel
CAN_FRAME_HEADER_STRUCT = struct.Struct("=IBB1xB")
# big-endian for pcapng
CAN_FRAME_HEADER_STRUCT_BE = struct.Struct(">IBB1xB")


log = logging.getLogger(__name__)


def parse_can_frame(
    cf: bytes, structure: struct.Struct = CAN_FRAME_HEADER_STRUCT
) -> Message:
    """Parse a CAN frame.

    :param cf: A CAN frame in socketcan format
    :return: A :class:`~can.Message` object with the parsed data
    """
    can_id, can_dlc, flags, data = dissect_can_frame(cf, structure)

    # EXT, RTR, ERR flags -> boolean attributes
    #   /* special address description flags for the CAN_ID */
    #   #define CAN_EFF_FLAG 0x80000000U /* EFF/SFF is set in the MSB */
    #   #define CAN_RTR_FLAG 0x40000000U /* remote transmission request */
    #   #define CAN_ERR_FLAG 0x20000000U /* error frame */
    is_extended_frame_format = bool(can_id & CAN_EFF_FLAG)
    is_remote_transmission_request = bool(can_id & CAN_RTR_FLAG)
    is_error_frame = bool(can_id & CAN_ERR_FLAG)
    is_fd = len(cf) == CANFD_MTU
    bitrate_switch = bool(flags & CANFD_BRS)
    error_state_indicator = bool(flags & CANFD_ESI)

    if is_extended_frame_format:
        # log.debug("CAN: Extended")
        # TODO does this depend on SFF or EFF?
        arbitration_id = can_id & 0x1FFFFFFF
    else:
        # log.debug("CAN: Standard")
        arbitration_id = can_id & 0x000007FF

    return Message(
        arbitration_id=arbitration_id,
        is_extended_id=is_extended_frame_format,
        is_remote_frame=is_remote_transmission_request,
        is_error_frame=is_error_frame,
        is_fd=is_fd,
        bitrate_switch=bitrate_switch,
        error_state_indicator=error_state_indicator,
        dlc=can_dlc,
        data=data,
    )


def _compose_arbitration_id(message: Message) -> int:
    can_id = message.arbitration_id
    if message.is_extended_id:
        log.debug("sending an extended id type message")
        can_id |= CAN_EFF_FLAG
    if message.is_remote_frame:
        log.debug("requesting a remote frame")
        can_id |= CAN_RTR_FLAG
    if message.is_error_frame:
        log.debug("sending error frame")
        can_id |= CAN_ERR_FLAG
    return can_id


def build_can_frame(
    msg: Message, structure: struct.Struct = CAN_FRAME_HEADER_STRUCT
) -> bytes:
    """CAN frame packing (see 'struct can_frame' in <linux/can.h>)

    :param msg: A :class:`~can.Message` object to convert to a CAN frame
    :return: A CAN frame in socketcan format
    """

    can_id = _compose_arbitration_id(msg)

    flags = 0

    # The socketcan code identify the received FD frame by the packet length.
    # So, padding to the data length is performed according to the message type (Classic / FD)
    if msg.is_fd:
        flags |= CANFD_FDF
        max_len = CANFD_MAX_DLEN
    else:
        max_len = CAN_MAX_DLEN

    if msg.bitrate_switch:
        flags |= CANFD_BRS
    if msg.error_state_indicator:
        flags |= CANFD_ESI

    data = bytes(msg.data).ljust(max_len, b"\x00")

    if msg.is_remote_frame:
        data_len = msg.dlc
    else:
        data_len = min(i for i in can.util.CAN_FD_DLC if i >= len(msg.data))
    header = structure.pack(can_id, data_len, flags, msg.dlc)
    return header + data


def is_frame_fd(frame: bytes) -> bool:
    # According to the SocketCAN implementation the frame length
    # should indicate if the message is FD or not (not the flag value)
    return len(frame) == CANFD_MTU


def dissect_can_frame(
    frame: bytes, structure: struct.Struct = CAN_FRAME_HEADER_STRUCT
) -> Tuple[int, int, int, bytes]:
    """Dissect a CAN frame into its components.

    :param frame: A CAN frame in socketcan format
    :return: Tuple of (CAN ID, CAN DLC, flags, data)
    """

    can_id, data_len, flags, len8_dlc = structure.unpack_from(frame)

    if data_len not in can.util.CAN_FD_DLC:
        data_len = min(i for i in can.util.CAN_FD_DLC if i >= data_len)

    can_dlc = data_len

    if not is_frame_fd(frame):
        # Flags not valid in non-FD frames
        flags = 0

        if data_len == CAN_MAX_DLEN and CAN_MAX_DLEN < len8_dlc <= CAN_MAX_RAW_DLC:
            can_dlc = len8_dlc

    return can_id, can_dlc, flags, frame[8 : 8 + data_len]

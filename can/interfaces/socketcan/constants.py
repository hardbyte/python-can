"""
Defines shared CAN constants.
"""

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

SIOCGIFNAME = 0x8910
SIOCGIFINDEX = 0x8933
SIOCGSTAMP = 0x8906
EXTFLG = 0x0004

CANFD_BRS = 0x01
CANFD_ESI = 0x02

CANFD_MTU = 72

STD_ACCEPTANCE_MASK_ALL_BITS = 2 ** 11 - 1
MAX_11_BIT_ID = STD_ACCEPTANCE_MASK_ALL_BITS

EXT_ACCEPTANCE_MASK_ALL_BITS = 2 ** 29 - 1
MAX_29_BIT_ID = EXT_ACCEPTANCE_MASK_ALL_BITS

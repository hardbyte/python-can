#!/usr/bin/python
# **********************************************************************
# File Name: server_commands.py
# Author(s): Mark C. <markc@dgtech.com>
# Target Project: BEACON Python
# Description: Part of dg_gryphon_protocol Python module
# Notes:
# **********************************************************************
#

"""DG gryphon protocol module

This package implements gryphon protocol

class structure
 class BEACON
 class GryphonReadThread
 class Gryphon
   class GryphonProtocolSD
   class GryphonProtocolFT
   class GryphonProtocolSDSERVER
   class GryphonProtocolSDCARD
   class GryphonProtocolCMD
   class GryphonProtocolLINServer
   class GryphonProtocolUSDTServer
   class GryphonProtocolResp
   class GryphonProtocolModFilter
   class GryphonProtocolSetFilterMode
   class GryphonProtocolSetDefaultFilter
   class GryphonProtocolFilterCondition
   class GryphonProtocolDictKeys
   class GryphonProtocolDefines

Version:
    Release 1.1 of 20190731

Dependencies:

Fixed Bugs:
    1.

Caveats:
    1. Tested only with Ubuntu 16.04
    2. Tested only with python 2.7.12
    3. Requires python package ...

Known issues:
    1.

Yet To Be Completed (TODO):
    +

.. _Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

"""

# from dg_timeout import timeout
import os
import datetime

# import Queue  # for read thread
import collections  # for incoming packets
import socket

# import json
import sys

# import functools
# import time
import signal
import threading

# from stackoverflow - How to set timeout on python's socket recv method?
# at http://stackoverflow.com/questions/2719017/how-to-set-timeout-on-pythons-socket-recv-method
import select
import struct  # for floating point number
import six  # manages compatibilty between Python 2.7 and Python 3.3+

# import ticker  # for Windows alarm signal
#
# ----------------------------------------------------------------------
# pylint: disable=too-many-lines
# ----------------------------------------------------------------------
#
GRYPHON_THREADED_CLIENT = None


def listntohs(data):
    """convert string network to host short

    Args:
        data array

    Pre:
        None.

    Post:
        None.

    Returns:
        short

    Raises:
        none
    """
    return (ord(data[0]) * 256) + ord(data[1])


def listntohl(data):
    """convert string network to host long

    Args:
        data array

    Pre:
        None.

    Post:
        None.

    Returns:
        short

    Raises:
        none
    """
    return (
        (ord(data[0]) * 1024)
        + (ord(data[1]) * 512)
        + (ord(data[2]) * 256)
        + ord(data[3])
    )


class GryphonProtocolSD:
    """SD defines
    """

    #
    # ----------------------------------------------------------------------
    # pylint: disable=too-few-public-methods
    # ----------------------------------------------------------------------
    #
    # /* source/destinations: */
    SD_CARD = 0x01  # /* (vehicle) network interface */
    SD_SERVER = 0x02
    SD_CLIENT = 0x03
    SD_KNOWN = 0x10  # /* Client ID >= are well known */
    SD_SCHED = 0x10  # /* scheduler */
    SD_SCRIPT = 0x20  # /* script processor */
    SD_PGM = 0x21  # /* Program loader */
    SD_USDT = 0x22
    SD_BLM = 0x23  # /* Bus Load Monitoring */
    SD_LIN = 0x24  # /* LIN extensions */
    SD_FLIGHT = 0x25  # /* Flight Recorder */
    SD_LOGGER = 0x25  # /* Data logger */
    SD_RESP = 0x26  # /* Message Response */
    SD_IOPWR = 0x27  # /* VNG / Compact Gryphon I/O & power */
    SD_UTIL = 0x28  # /* Miscellaneous utility commands   */
    SD_CNVT = 0x29  # /* Signal conversion commands       */
    SD_J1939TP = 0x30  # /* J1939 Transport Protocol */
    CH_BROADCAST = 0xFF  # /* Special channel ID for broadcast messages */


class GryphonProtocolFT:
    """FT defines
    """

    #
    # ----------------------------------------------------------------------
    # pylint: disable=too-few-public-methods
    # ----------------------------------------------------------------------
    #
    # /* frame types: */
    FT_CMD = 0x01  # /* command to initiate some action */
    FT_RESP = 0x02  # /* response to a command */
    FT_DATA = 0x03  # /* (vehicle) network data */
    FT_EVENT = 0x04  # /* notification of an event */
    FT_MISC = 0x05  # /* misc data */
    FT_TEXT = 0x06  # /* null-terminated ASCII strings */
    FT_SIG = 0x07  # /* (vehicle) network signals */
    MAX_TEXT = 0xFF  # /* Maximum FT_TEXT string length */


class GryphonProtocolSDSERVER:
    """card command bytes "B"
    """

    #
    # ----------------------------------------------------------------------
    # pylint: disable=too-few-public-methods
    # ----------------------------------------------------------------------
    #
    # /* SD_SERVER command types: */
    BCMD_SERVER_REG = 0x50  # /* register connection */
    BCMD_SERVER_SET_SORT = 0x51  # /* set sorting behavior */
    BCMD_SERVER_SET_OPT = 0x52  # /* set type of optimization */
    BCMD_SERVER_SET_TIMED_XMIT = 0x53  # /* set to time xmit data frame msgs */
    BCMD_SERVER_SET_SERVICE = 0x54  # /* set the higher-layer protocol service */
    BCMD_J1939_ADDR_CLAIM = 0x55  # /* claim J1939 address */


class GryphonProtocolSDCARD:
    """card command bytes "B"
    """

    #
    # ----------------------------------------------------------------------
    # pylint: disable=too-few-public-methods
    # ----------------------------------------------------------------------
    #
    # /* SD_CARD command types: */
    BCMD_CARD_SET_SPEED = 0x40  # /* set peripheral speed */
    BCMD_CARD_GET_SPEED = 0x41  # /* get peripheral speed */
    BCMD_CARD_SET_FILTER = 0x42  # /* set filter to pass or block all */
    BCMD_CARD_GET_FILTER = 0x43  # /* get a pass/block filter */
    BCMD_CARD_TX = 0x44  # /* transmit message */
    BCMD_CARD_TX_LOOP_ON = 0x45  # /* set transmit loopback on */
    BCMD_CARD_TX_LOOP_OFF = 0x46  # /* set transmit loopback off */
    BCMD_CARD_IOCTL = 0x47  # /* device driver ioctl pass-through */
    BCMD_CARD_ADD_FILTER = 0x48  # /* add a pass/block filter */
    BCMD_CARD_MODIFY_FILTER = 0x49  # /* modify a pass/block filter */
    BCMD_CARD_GET_FILTER_HANDLES = 0x4A  # /* get a list of filters */
    BCMD_CARD_SET_DEFAULT_FILTER = 0x4B  # /* set the default action */
    BCMD_CARD_GET_DEFAULT_FILTER = 0x4C  # /* get the defautl action */
    BCMD_CARD_SET_FILTER_MODE = 0x4D  # /* set the client data mode */
    BCMD_CARD_GET_FILTER_MODE = 0x4E  # /* get the client data mode */
    BCMD_CARD_GET_EVNAMES = 0x4F  # /* get event names */
    BCMD_CARD_GET_SPEEDS = 0x50  # /* get speed definitions */


class GryphonProtocolCMD:
    """protocol command bytes "B"
    """

    #
    # ----------------------------------------------------------------------
    # pylint: disable=too-few-public-methods
    # ----------------------------------------------------------------------
    #
    # /* generic (all SD type) commands: values 0x00 to 0x3f */
    BCMD_INIT = 0x01  # /* initialize target */
    # CMD_GET_STAT = 0x02    # /* request status */
    BCMD_GET_CONFIG = 0x03  # /* request configuration info */
    BCMD_EVENT_ENABLE = 0x04  # /* Enable event type */
    BCMD_EVENT_DISABLE = 0x05  # /* Disable event type */
    BCMD_GET_TIME = 0x06  # /* Get current value of timestamp */
    BCMD_GET_RXDROP = 0x07  # /* Get count of Rx msgs dropped */
    BCMD_RESET_RXDROP = 0x08  # /* Set count of Rx msgs dropped to zero */
    BCMD_BCAST_ON = 0x09  # /* broadcasts on */
    BCMD_BCAST_OFF = 0x0A  # /* broadcasts off */
    BCMD_SET_TIME = 0x0B  # /* set time */


class GryphonProtocolLINServer:
    """LIN command bytes "B"
    """

    #
    # ----------------------------------------------------------------------
    # pylint: disable=too-few-public-methods
    # ----------------------------------------------------------------------
    #
    BCMD_LDF_DESC = 0xB8
    BCMD_LDF_UPLOAD = 0xB9
    BCMD_LDF_LIST = 0xBA
    BCMD_LDF_DELETE = 0xBB
    BCMD_LDF_PARSE = 0xBC
    BCMD_GET_LDF_INFO = 0xBD
    BCMD_GET_NODE_NAMES = 0xBE
    BCMD_EMULATE_NODES = 0xBF
    BCMD_GET_FRAMES = 0xB0
    BCMD_GET_FRAME_INFO = 0xC1
    BCMD_GET_SIGNAL_INFO = 0xC2
    BCMD_GET_SIGNAL_DETAIL = 0xC3
    BCMD_GET_ENCODING_INFO = 0xC4
    BCMD_GET_SCHEDULES = 0xC5
    BCMD_START_SCHEDULE = 0xC6
    BCMD_STOP_SCHEDULE = 0xC7
    BCMD_STORE_DATA = 0xC8
    BCMD_SEND_ID = 0xC9
    BCMD_SEND_ID_DATA = 0xCA
    BCMD_SAVE_SESSION = 0xCB
    BCMD_RESTORE_SESSION = 0xCC
    BCMD_GET_NODE_SIGNALS = 0xCD
    BGRESETHC08 = "11800009"


class GryphonProtocolCNVTServer:
    """cnvt command bytes "B"
    """

    #
    # ----------------------------------------------------------------------
    # pylint: disable=too-few-public-methods
    # ----------------------------------------------------------------------
    #
    BCMD_CNVT_GET_VALUES = 0x78
    BCMD_CNVT_GET_UNITS = 0x79
    BCMD_CNVT_SET_VALUES = 0x7A
    BCMD_DESTROY_SESSION = 0x7B
    BCMD_READ_CNVT_CONFIG = 0x7C
    BCMD_CNVT_REQ_VALUES = 0x7D
    BCMD_CNVT_REQ_SUSPEND = 0x7E
    BCMD_CNVT_REQ_RESUME = 0x7F
    BCMD_CNVT_REQ_MODIFY = 0x80
    BCMD_CNVT_GET_MSG_NAMES = 0x81
    BCMD_CNVT_GET_SIG_NAMES = 0x82
    BCMD_CNVT_REQ_CANCEL = 0x83


class GryphonProtocolKWPIOCTL:
    """code for KWP ISO9141 ioctl
    """

    #
    # ----------------------------------------------------------------------
    # pylint: disable=too-few-public-methods
    # ----------------------------------------------------------------------
    #
    GKWPSETPTIMES = 0x11700011  # /* 16 */
    GKWPSETWTIMES = 0x11700010  # /* 20 */
    GKWPDOWAKEUP = 0x11700008  # /* 0 */
    GKWPGETBITTIME = 0x11700101  # /* 2 */
    GKWPSETBITTIME = 0x11700102  # /* 2 vsoni */
    GKWPSETNODEADDR = 0x11700104  # /* 1 vsoni */
    GKWPGETNODETYPE = 0x11700105  # /* 1 */
    GKWPSETNODETYPE = 0x11700106  # /* 1 vsoni */
    GKWPMONITOR = 0x00
    GKWPECU = 0x01
    GKWPTESTER = 0x02
    GKWPSETWAKETYPE = 0x11700108  # /* 1 */
    GKWPFAST = 0x00
    GKWPFIVEBAUD = 0x02
    GKWPSETTARGADDR = 0x1170010A  # /* 1 */
    GKWPSETKEYBYTES = 0x1170010C  # /* 2 */
    GKWPSETSTARTREQ = 0x1170010E  # /* 5 */
    GKWPSETSTARTRESP = 0x11700110  # /* 7 */
    GKWPSETPROTOCOL = 0x11700112  # /* 1 vsoni */
    GKWPKWP2000 = 0x01
    GKWPISO9141FORD = 0x02
    GKWPGETLASTKEYBYTES = 0x11700201  # /* 2 */
    GKWPSETLASTKEYBYTES = 0x11700202  # /* 2 */


class GryphonProtocolLINIOCTL:
    """code for LIN ioctl
    """

    #
    # ----------------------------------------------------------------------
    # pylint: disable=too-few-public-methods
    # ----------------------------------------------------------------------
    #
    GLINGETBITRATE = 0x11C00001  # 2 bytes returned
    GLINSETBITRATE = 0x11C00002  # 2
    GLINGETBRKSPACE = 0x11C00003  # 1
    GLINSETBRKSPACE = 0x11C00004  # 1
    GLINGETBRKMARK = 0x11C00005  # 1
    GLINSETBRKMARK = 0x11C00006  # 1
    GLINGETIDDELAY = 0x11C00007  # 1
    GLINSETIDDELAY = 0x11C00008  # 1
    GLINGETRESPDELAY = 0x11C00009  # 1
    GLINSETRESPDELAY = 0x11C0000A  # 1
    GLINGETINTERBYTE = 0x11C0000B  # 1
    GLINSETINTERBYTE = 0x11C0000C  # 1
    GLINGETWAKEUPDELAY = 0x11C0000D  # 1
    GLINSETWAKEUPDELAY = 0x11C0000E  # 1
    GLINGETWAKEUPTIMEOUT = 0x11C0000F  # 1
    GLINSETWAKEUPTIMEOUT = 0x11C00010  # 1
    GLINGETWUTIMOUT3BR = 0x11C00011  # 2
    GLINSETWUTIMOUT3BR = 0x11C00012  # 2
    GLINSENDWAKEUP = 0x11C00013  # 0
    GLINGETMODE = 0x11C00014  # 1
    GLINSETMODE = 0x11C00015  # 1
    GLINGETSLEW = 0x11C00016  # 1
    GLINSETSLEW = 0x11C00017  # 1
    GLINADDSCHED = 0x11C00018  # var., 41+
    GLINGETSCHED = 0x11C00019  # var., 41+
    GLINGETSCHEDSIZE = 0x11C0001A  # 2
    GLINDELSCHED = 0x11C0001B  # 32
    GLINACTSCHED = 0x11C0001C  # 32
    GLINDEACTSCHED = 0x11C0001D  # 32
    GLINGETACTSCHED = 0x11C0001E  # 32
    GLINGETNUMSCHEDS = 0x11C0001F  # 2
    GLINGETSCHEDNAMES = 0x11C00020  # var., 32 * n
    GLINSETFLAGS = 0x11C00021  # var., 2 + n
    GLINGETAUTOCHECKSUM = 0x11C00022  # 1 Saint2 get automatic checksum, BC 03
    GLINSETAUTOCHECKSUM = 0x11C00023  # 1 Saint2 set automatic checksum, BC 03
    GLINGETAUTOPARITY = 0x11C00024  # 1 Saint2 get automatic parity, BC 04
    GLINSETAUTOPARITY = 0x11C00025  # 1 Saint2 set automatic parity, BC 04
    GLINGETSLAVETABLEENABLE = 0x11C00026  # var., 2 + n
    GLINSETSLAVETABLEENABLE = 0x11C00027  # var., 2 + n
    GLINGETFLAGS = 0x11C00028  # var., 2 + n
    GLINGETWAKEUPMODE = 0x11C00029  # 1 Saint2 vs. Gryphon wakeup and sleep modes
    GLINSETWAKEUPMODE = 0x11C0002A  # 1 Saint2 vs. Gryphon wakeup and sleep modes
    GLINGETMASTEREVENTENABLE = 0x11C0002B  # 1
    GLINSETMASTEREVENTENABLE = 0x11C0002C  # 1
    GLINGETNSLAVETABLE = 0x11C0002D  # 1
    GLINGETSLAVETABLEPIDS = 0x11C0002E  # var.
    GLINGETSLAVETABLE = 0x11C0002F  # var.
    GLINSETSLAVETABLE = 0x11C00030  # var.
    GLINCLEARSLAVETABLE = 0x11C00031  # 1
    GLINCLEARALLSLAVETABLE = 0x11C00032  # 0
    GLINGETONESHOT = 0x11C00033  # var.
    GLINSETONESHOT = 0x11C00034  # var.
    GLINCLEARONESHOT = 0x11C00035  # 0


class GryphonProtocolDDIOCTL:
    """code for dd ioctl
    """

    #
    # ----------------------------------------------------------------------
    # pylint: disable=too-few-public-methods
    # ----------------------------------------------------------------------
    #
    GDLYGETHIVALUE = 0x11D50001  # 4 get the high water value
    GDLYSETHIVALUE = 0x11D50002  # 4 set the high water value
    GDLYGETLOVALUE = 0x11D50003  # 4 get the low water value
    GDLYSETLOVALUE = 0x11D50004  # 4 set the low water value
    GDLYGETHITIME = 0x11D50005  # 4 get the high water time
    GDLYSETHITIME = 0x11D50006  # 4 set the high water time
    GDLYGETLOTIME = 0x11D50007  # 4 get the low water time
    GDLYSETLOTIME = 0x11D50008  # 4 set the low water time
    GDLYGETLOREPORT = 0x11D50009  # 4 get the low water report flag
    GDLYFLUSHSTREAM = 0x11D5000A  # 2 flush the delay buffer
    GDLYINITSTREAM = 0x11D5000B  # 2 set default hi & lo water marks
    GDLYPARTIALFLUSHSTREAM = 0x11D5000C  # 4 flush the delay buffer


class GryphonProtocolUSDTServer:
    """USDT command bytes "B"
    """

    #
    # ----------------------------------------------------------------------
    # pylint: disable=too-few-public-methods
    # ----------------------------------------------------------------------
    #
    BCMD_USDT_REGISTER = 0xB0
    BCMD_USDT_SET_FUNCTIONAL = 0xB1
    BCMD_USDT_SET_EXTENDED = 0xB1
    BCMD_USDT_SET_STMIN_MULT = 0xB2
    BCMD_USDT_SET_STMIN_FC = 0xB3
    BCMD_USDT_GET_STMIN_FC = 0xB4
    BCMD_USDT_SET_BSMAX_FC = 0xB5
    BCMD_USDT_GET_BSMAX_FC = 0xB6
    BCMD_USDT_REGISTER_NON = 0xB7
    BCMD_USDT_SET_STMIN_OVERRIDE = 0xB8
    BCMD_USDT_GET_STMIN_OVERRIDE = 0xB9
    #
    # ----------------------------------------------------------------------
    # pylint: disable=invalid-name
    # ----------------------------------------------------------------------
    #
    BCMD_USDT_ACTIVATE_STMIN_OVERRIDE = 0xBA


class GryphonProtocolSched:
    """sched commands
        see sched.h
    """

    #
    # ----------------------------------------------------------------------
    # pylint: disable=too-few-public-methods
    # ----------------------------------------------------------------------
    #
    BCMD_SCHED_TX = 0x70
    BCMD_SCHED_KILL_TX = 0x71
    BCMD_SCHED_STOP_TX = 0x71
    BCMD_SCHED_MSG_REPLACE = 0x72
    BCMD_DELAY_TX = 0x73
    BCMD_SCHED_GET_IDS = 0x74
    GSCHEDDONE = 0x04
    EVENT_SCHED_DONE = 0x04


class GryphonProtocolResp:
    """response codes
    """

    #
    # ----------------------------------------------------------------------
    # pylint: disable=too-few-public-methods
    # ----------------------------------------------------------------------
    #
    # /* response frame (FT_RESP) response field definitions: */
    RESP_OK = 0x00  # /* no error */
    RESP_UNKNOWN_ERR = 0x01  # /* unknown error */
    RESP_UNKNOWN_CMD = 0x02  # /* unrecognised command */
    RESP_UNSUPPORTED = 0x03  # /* unsupported command */
    RESP_INVAL_CHAN = 0x04  # /* invalid channel specified */
    RESP_INVAL_DST = 0x05  # /* invalid destination */
    RESP_INVAL_PARAM = 0x06  # /* invalid parameters */
    RESP_INVAL_MSG = 0x07  # /* invalid message */
    RESP_INVAL_LEN = 0x08  # /* invalid length field */
    RESP_TX_FAIL = 0x09  # /* transmit failed */
    RESP_RX_FAIL = 0x0A  # /* receive failed */
    RESP_AUTH_FAIL = 0x0B
    RESP_MEM_ALLOC_ERR = 0x0C  # /* memory allocation error */
    RESP_TIMEOUT = 0x0D  # /* command timed out */
    RESP_UNAVAILABLE = 0x0E
    RESP_BUF_FULL = 0x0F  # /* buffer full */
    RESP_NO_SUCH_JOB = 0x10
    RESP_NO_ROOM = 0x11  # /* not enough room on the disk */
    RESP_BUSY = 0x12  # /* device or object is busy */
    NO_FRAME_DATA = 0x13  # /* no frame data */


class GryphonProtocolInit:
    """filter defines
    """

    #
    # ----------------------------------------------------------------------
    # pylint: disable=too-few-public-methods
    # pylint: disable=invalid-name
    # ----------------------------------------------------------------------
    #
    # /* Actions available via BCMD_INIT */
    ALWAYS_INIT = 0
    INIT_IF_NOT_PREVIOUSLY_INITIALIZED = 1
    INIT_SCHEDULER = 0  # init sched chan=0, other channels are channel number


class GryphonProtocolModFilter:
    """mod filter defines
    """

    #
    # ----------------------------------------------------------------------
    # pylint: disable=too-few-public-methods
    # ----------------------------------------------------------------------
    #
    # /* Actions available via CMD_CARD_MODIFY_FILTER */
    DELETE_FILTER = 0
    ACTIVATE_FILTER = 1
    DEACTIVATE_FILTER = 2


class GryphonProtocolSetFilterMode:
    """filter mode defines
    """

    #
    # ----------------------------------------------------------------------
    # pylint: disable=too-few-public-methods
    # ----------------------------------------------------------------------
    #
    # /* Modes available via CMD_CARD_SET_FILTERING_MODE */
    FILTER_OFF_PASS_ALL = 3
    FILTER_OFF_BLOCK_ALL = 4
    FILTER_ON = 5


class GryphonProtocolSetDefaultFilter:
    """default filter
    """

    #
    # ----------------------------------------------------------------------
    # pylint: disable=too-few-public-methods
    # ----------------------------------------------------------------------
    #
    # /* Modes available via CMD_CARD_SET_DEFAULT_FILTER */
    DEFAULT_FILTER_BLOCK = 0
    DEFAULT_FILTER_PASS = 1


class GryphonProtocolFilterFlags:
    """filter flags
    """

    #
    # ----------------------------------------------------------------------
    # pylint: disable=too-few-public-methods
    # ----------------------------------------------------------------------
    #
    # /* for CMD_CARD_ADD_FILTER */
    FILTER_FLAG_BLOCK = 0
    FILTER_FLAG_PASS = 1
    FILTER_FLAG_INACTIVE = 0
    FILTER_FLAG_ACTIVE = 2
    FILTER_FLAG_AND_BLOCKS = 0
    FILTER_FLAG_OR_BLOCKS = 4
    FILTER_FLAG_SAMPLING_INACTIVE = 0
    FILTER_FLAG_SAMPLING_ACTIVE = 8


class GryphonProtocolFilterDataType:
    """filter flags
    """

    #
    # ----------------------------------------------------------------------
    # pylint: disable=too-few-public-methods
    # ----------------------------------------------------------------------
    #
    # /* for CMD_CARD_ADD_FILTER */
    FILTER_DATA_TYPE_HEADER_FRAME = 0
    FILTER_DATA_TYPE_HEADER = 1
    FILTER_DATA_TYPE_DATA = 2
    FILTER_DATA_TYPE_EXTRA_DATA = 3
    FILTER_EVENT_TYPE_EXTRA_HEADER = 4
    FILTER_EVENT_TYPE_EXTRA_DATA = 5


class GryphonProtocolEventIDs:
    """event IDs
    """

    #
    # ----------------------------------------------------------------------
    # pylint: disable=too-few-public-methods
    # ----------------------------------------------------------------------
    #
    # from gmsg.h
    EVENT_INIT = 1
    EVENT_SPD = 2
    EVENT_CLIENT_GONE = 3
    EVENT_MSG_SENT = 4

    EVENT_ADDR_LOST = 5
    # from sched.h
    EVENT_SCHED_DONE = 4


class GryphonProtocolFilterCondition:
    """filter condition operator defines
    """

    #
    # ----------------------------------------------------------------------
    # pylint: disable=too-few-public-methods
    # ----------------------------------------------------------------------
    #
    # /* Filter and Frame Responder Condition operators */
    BIT_FIELD_CHECK = 0
    SVALUE_GT = 1
    SVALUE_GE = 2
    SVALUE_LT = 3
    SVALUE_LE = 4
    VALUE_EQ = 5
    VALUE_NE = 6
    UVALUE_GT = 7
    UVALUE_GE = 8
    UVALUE_LT = 9
    UVALUE_LE = 10
    DIG_LOW_TO_HIGH = 11
    DIG_HIGH_TO_LOW = 12
    DIG_TRANSITION = 13


class GryphonProtocolMSGRESP:
    """message responder commands
    """

    #
    # ----------------------------------------------------------------------
    # pylint: disable=too-few-public-methods
    # ----------------------------------------------------------------------
    #
    BCMD_MSGRESP_ADD = 0xB0
    BCMD_MSGRESP_GET = 0xB1
    BCMD_MSGRESP_MODIFY = 0xB2
    BCMD_MSGRESP_GET_HANDLES = 0xB3


class GryphonProtocolMSGRESPActions:
    """message responder
    """

    #
    # ----------------------------------------------------------------------
    # pylint: disable=too-few-public-methods
    # ----------------------------------------------------------------------
    #
    FR_RESP_AFTER_EVENT = 0
    FR_RESP_AFTER_PERIOD = 1
    FR_IGNORE_DURING_PER = 2
    FR_PERIOD_MSGS = 0x10
    FR_DELETE = 0x20
    FR_DEACT_ON_EVENT = 0x40
    FR_DEACT_AFTER_PER = 0x80
    MSGRESP_DELETE_RESPONSE = 0
    MSGRESP_ACTIVATE_RESPONSE = 1
    MSGRESP_DEACTIVATE_RESPONSE = 2


class GryphonProtocolDictKeys:
    """code for dictionaries (i.e. assoc arrays)
    """

    #
    # ----------------------------------------------------------------------
    # pylint: disable=too-few-public-methods
    # ----------------------------------------------------------------------
    #
    SRC = "src"
    SRCCHAN = "srcchan"
    DST = "dst"
    DSTCHAN = "dstchan"
    LEN = "msglen"
    FRAMETYPE = "frametype"
    CMD = "cmd"
    DATASTR = "datastr"
    FTDATA = "ftdata"
    CLIENT_ID = "client_id"
    STATUS = "status"
    PRIV = "priv"
    CONTEXT = "context"
    RAWDATA = "rawdata"
    SET_IOCTL = "set_ioctl"
    GET_IOCTL = "get_ioctl"
    N_PRESET = "n_preset"
    PRESET_SIZE = "preset_size"
    PRESETS = "presets"
    BTR = "btr"
    EVNAMES = "event_names"
    EVENT_ID = "event_id"
    EVENT_NAME = "event_name"
    MODE = "mode"


class GryphonProtocolIOCTL:
    """code for ioctl
    """

    #
    # ----------------------------------------------------------------------
    # pylint: disable=too-few-public-methods
    # ----------------------------------------------------------------------
    #
    IOCTL_GINIT = 0x11100001  # 0 bytes returned
    IOCTL_GLOOPON = 0x11100002  # 0
    IOCTL_GLOOPOFF = 0x11100003  # 2
    IOCTL_GGETHWTYPE = 0x11100004  # 2
    IOCTL_GGETREG = 0x11100005  # 4
    IOCTL_GSETREG = 0x11100006  # 4
    IOCTL_GGETRXCOUNT = 0x11100007  # 4
    IOCTL_GSETRXCOUNT = 0x11100008  # 4
    IOCTL_GGETTXCOUNT = 0x11100009  # 4
    IOCTL_GSETTXCOUNT = 0x1110000A  # 4
    IOCTL_GGETRXDROP = 0x1110000B  # 4
    IOCTL_GSETRXDROP = 0x1110000C  # 4
    IOCTL_GGETTXDROP = 0x1110000D  # 4
    IOCTL_GSETTXDROP = 0x1110000E  # 4
    IOCTL_GGETRXBAD = 0x1110000F  # 4
    IOCTL_GGETTXBAD = 0x11100011  # 4
    IOCTL_GGETCOUNTS = 0x11100013  # 60
    IOCTL_GGETBLMON = 0x11100014  # 1
    IOCTL_GSETBLMON = 0x11100015  # 1
    IOCTL_GGETERRLEV = 0x11100016  # 1
    IOCTL_GSETERRLEV = 0x11100017  # 1
    IOCTL_GGETBITRATE = 0x11100018  # 4
    IOCTL_GGETRAM = 0x11100019  # 3
    IOCTL_GSETRAM = 0x1110001A  # 3
    IOCTL_GSKIPCHAN = 0x1110001B  # 0
    IOCTL_GPROCESSCHAN = 0x1110001C  # 0
    IOCTL_GFREEBUFFERED = 0x1110001D  # 0
    IOCTL_GGETFASTBITRATE = 0x1110001E  # 4
    IOCTL_GCANGETMODE = 0x11200005  # 1
    IOCTL_GCANSETMODE = 0x11200006  # 1
    IOCTL_GSETBITRATE = 0x11100020  # 8
    IOCTL_GSETFASTBITRATE = 0x11100025  # 8
    IOCTL_GGETSAMPLEPOINT = 0x11100021  # 4
    IOCTL_GGETFASTSAMPLEPOINT = 0x11100027  # 4
    IOCTL_GGETSJW = 0x11100023  # 1
    IOCTL_GSETSJW = 0x11100024  # 1
    IOCTL_GGETFASTSJW = 0x11100028  # 1
    IOCTL_GSETFASTSJW = 0x11100029  # 1
    IOCTL_GETINTTERM = 0x11250010  # 1
    IOCTL_SETINTTERM = 0x11250011  # 1
    IOCTL_GCANGETPHYSTYPE = 0x11260001  # 1
    IOCTL_GCANGETAUTOACK = 0x11260003  # 1
    IOCTL_GCANSETAUTOACK = 0x11260004  # 1
    IOCTL_GCANGETLISTEN = 0x11260005  # 1
    IOCTL_GCANSETLISTEN = 0x11260006  # 1
    IOCTL_GCANSWGETMODE = 0x11220001  # 1
    IOCTL_GCANSWSETMODE = 0x11220002  # 1


class GryphonProtocolRxTxMode:
    """code for rx tx mode
        see gmsg.h
    """

    #
    # ----------------------------------------------------------------------
    # pylint: disable=too-few-public-methods
    # ----------------------------------------------------------------------
    #
    MODE_REMOTE = 0x10
    MODE_LOCAL = 0x20
    MODE_RX = 0x40
    MODE_TX = 0x80
    MODE_INTERNAL = 0x01
    MODE_NOMUX = 0x02
    MODE_COMBINED = 0x04


class GryphonProtocolCANMode:
    """CAN modes
    """

    #
    # ----------------------------------------------------------------------
    # pylint: disable=too-few-public-methods
    # ----------------------------------------------------------------------
    #
    MODE_CAN = 0x00
    MODE_CANFD = 0x01
    MODE_CANFD_PREISO = 0x02


class GryphonProtocolDefs:
    """code for defs
        see gmsg.h
    """

    #
    # ----------------------------------------------------------------------
    # pylint: disable=too-few-public-methods
    # ----------------------------------------------------------------------
    #
    MAXPAYLOAD = 7168


#
# ----------------------------------------------------------------------
# pylint: disable=too-many-ancestors
# pylint: disable=too-few-public-methods
# ----------------------------------------------------------------------
#
class GryphonProtocolCommands(
    GryphonProtocolSDCARD,
    GryphonProtocolSDSERVER,
    GryphonProtocolCMD,
    GryphonProtocolLINServer,
    GryphonProtocolCNVTServer,
    GryphonProtocolUSDTServer,
    GryphonProtocolSched,
    GryphonProtocolMSGRESP,
):
    """all commands, for convenience
    """


class GryphonProtocolDefines(
    GryphonProtocolCommands,
    GryphonProtocolFT,
    GryphonProtocolSD,
    GryphonProtocolDictKeys,
    GryphonProtocolResp,
    GryphonProtocolInit,
    GryphonProtocolModFilter,
    GryphonProtocolSetFilterMode,
    GryphonProtocolSetDefaultFilter,
    GryphonProtocolFilterFlags,
    GryphonProtocolFilterDataType,
    GryphonProtocolFilterCondition,
    GryphonProtocolLINIOCTL,
    GryphonProtocolKWPIOCTL,
    GryphonProtocolDDIOCTL,
    GryphonProtocolIOCTL,
    GryphonProtocolRxTxMode,
    GryphonProtocolEventIDs,
    GryphonProtocolMSGRESPActions,
    GryphonProtocolDefs,
):
    """all defines, all commands, for convenience
    """


#
# ----------------------------------------------------------------------
# pylint: enable=too-many-ancestors
# pylint: enable=too-few-public-methods
# ----------------------------------------------------------------------
#


class TooManyLoops(Exception):
    """too many loops looking for response
    """

    def __init__(self, arg1=None):
        self.arg1 = arg1
        super(TooManyLoops, self).__init__(arg1)


class TimeOut(Exception):
    """timeout exception
    """

    def __init__(self, arg1=None):
        self.arg1 = arg1
        super(TimeOut, self).__init__(arg1)


def handle_timeout(signal_in, frame_in):
    """timeout signal callback
    """
    _, _ = signal_in, frame_in
    _ = _
    raise TimeOut()


class GryphonQueue:
    """queue

    Attributes:
        self.mylock - threading Lock
        self.myq - queue of rx messages
        self.name - name of queue
        self.maxlen - max length
        self.overflow - queue overflow
        self.not_empty_event - not empty event
    """

    def __init__(self, name="Unknown", maxlen=1000):
        """init
        """
        self.mylock = threading.Lock()
        self.myq = collections.deque(maxlen=maxlen)
        self.name = name
        self.maxlen = maxlen
        self.overflow = False
        self.not_empty_event = threading.Event()  # use this to indicate myq not empty
        self.not_empty_event.clear()

    def __del__(self):
        """del
        """
        self.mylock.acquire(True)
        self.myq.clear()
        self.mylock.release()

    def put(self, item):
        """put
        Args:
            item - item to add

        Pre:
            if locked, waits for unlock

        Post:
            item is on left of queue
            if overflow, self.overflow is True
            queue not empty
            lock is unlocked
        """
        self.mylock.acquire(True)
        if len(self.myq) >= self.maxlen:
            self.overflow = True
        self.myq.appendleft(item)
        self.not_empty_event.set()
        self.mylock.release()

    def is_overflow(self):
        """return True if deque is overflowed, clear overflow if needed
        Pre:
            None.

        Post:
            if self.overflow AND no overflow, self.overflow is False
            lock is unlocked

        Returns:
            True if current overflow
        """
        self.mylock.acquire(True)
        if (self.overflow) and (len(self.myq) < self.maxlen):
            # clear overflow
            self.overflow = False
        self.mylock.release()
        return self.overflow

    def flush(self):
        """flush queue
        Pre:
            None.

        Post:
            queue is empty
            self.overflow is False
            lock is unlocked
        """
        self.mylock.acquire(True)
        self.myq.clear()
        self.overflow = False
        self.mylock.release()

    def get(self, block=False, timeout=3.0):
        """master get
        Args:
            block - False will not block
            timeout - seconds to wait while blocked

        Pre:
            None.

        Post:
            IF no item
                if block, waited timeout seconds
            ELSE
                queue is one less item on right
            lock is unlocked

        Returns:
            None if no item
            item in queue

        Raises:
            IndexError - cannot read queue

        """
        #
        # ----------------------------------------------------------------------
        # pylint: disable=too-many-branches
        # ----------------------------------------------------------------------
        #
        item = None
        # TODO implement blocking
        timeout = float(timeout)
        if block:
            #
            # ------------------------------------------------------------------
            # pylint: disable=len-as-condition
            # ------------------------------------------------------------------
            #
            # 20190117 removing signal.SIGALRM
            # signal.signal(signal.SIGALRM, handle_timeout)
            # signal.alarm(timeout)

            # print "wating,  q name=%s" % self.name
            is_not_timeout = self.not_empty_event.wait(timeout)
            # six.print_("->>>>>>>>>>>>>-----------",is_not_timeout)
            if not is_not_timeout:
                # timed out
                item = None
            else:
                try:
                    self.mylock.acquire(True)
                    item = self.myq.pop()
                    # signal.alarm(0)  # SIGALRM
                    if len(self.myq) == 0:
                        self.not_empty_event.clear()
                except IndexError:
                    # TODO
                    self.not_empty_event.clear()  # TODO clear or not
                    raise IndexError
                finally:
                    self.mylock.release()
        else:
            #
            # ----------------------------------------------------------
            # pylint: disable=len-as-condition
            # ----------------------------------------------------------
            #
            item = None
            if self.not_empty_event.is_set():
                try:
                    self.mylock.acquire(True)
                    item = self.myq.pop()
                    if not self.myq:
                        self.not_empty_event.clear()
                except IndexError:
                    # TODO
                    raise IndexError
                finally:
                    self.mylock.release()
        return item

    def get_nonblock(self):
        """get non blocking
        Pre:
            None.

        Post:
            IF no item
                return None immediately
            ELSE
                queue is one less item on right
            lock is unlocked

        Returns:
            item, or return None if no item

        Raises:

        """
        #
        # ----------------------------------------------------------
        # pylint: disable=len-as-condition
        # ----------------------------------------------------------
        #
        item = None
        self.mylock.acquire(True)
        if len(self.myq) == 0:
            item = None
        try:
            item = self.myq.pop()
        except IndexError:
            # TODO
            raise IndexError
        finally:
            self.mylock.release()
        return item

    def qsize(self):
        """size of queue
        """
        return len(self.myq)


class GryphonReadThread(GryphonProtocolDefines):
    #
    # ----------------------------------------------------------------------
    # pylint: disable=too-many-ancestors
    # pylint: disable=too-many-instance-attributes
    # ----------------------------------------------------------------------
    #
    """read thread

    Attributes:
        self.client_id - client id
        self.sock - socket
        self.timeout - timeout for select()
        self.general_q - all messages
        self.event_q - events
        self.cmd_q - commands
        self.resp_q - responses
        self.misc_q - misc
        self.text_q - text
        self.sig_q - signals
        self.data_q - data
        self.queues - dict of queues one entry for each frame type
        self.thr1_kill_event - threading.Event()
        self.thr1 - returned from creating read thread
        GRYPHON_THREADED_CLIENT - global read thread

    """
    MAX_RETRY_LOOPS = 5

    def __init__(self, sock, timeout, maxlen=1000):
        """init

        Args:
            socket
            timeout
            max length of queue
        """
        #
        # ----------------------------------------------------------------------
        # pylint: disable=global-statement
        # ----------------------------------------------------------------------
        #
        # init the queue
        self.client_id = None
        self.sock = sock
        self.timeout = timeout

        """
        self.general_q = Queue.Queue()
        self.event_q = Queue.Queue()  # FT_EVENT /* notification of an event */
        self.cmd_q = Queue.Queue()  # FT_CMD /* command to initiate some action */
        self.resp_q = Queue.Queue()  # FT_RESP /* response to a command */
        self.misc_q = Queue.Queue()  # FT_MISC /* misc data */
        self.text_q = Queue.Queue()  # FT_TEXT /* null-terminated ASCII strings */
        self.sig_q = Queue.Queue()  # FT_SIG /* (vehicle) network signals */
        self.data_q = Queue.Queue()  # FT_DATA /* (vehicle) network data */
        """
        self.general_q = GryphonQueue(name="General", maxlen=maxlen)
        self.event_q = GryphonQueue(
            name="Event", maxlen=maxlen
        )  # FT_EVENT /* notification of an event */
        self.cmd_q = GryphonQueue(
            name="Req", maxlen=maxlen
        )  # FT_CMD /* command to initiate some action */
        self.resp_q = GryphonQueue(
            name="Resp", maxlen=maxlen
        )  # FT_RESP /* response to a command */
        self.misc_q = GryphonQueue(
            name="Misc", maxlen=maxlen
        )  # FT_MISC /* misc data */
        self.text_q = GryphonQueue(
            name="Text", maxlen=maxlen
        )  # FT_TEXT /* null-terminated ASCII strings */
        self.sig_q = GryphonQueue(
            name="Sig", maxlen=maxlen
        )  # FT_SIG /* (vehicle) network signals */
        self.data_q = GryphonQueue(
            name="Data", maxlen=maxlen
        )  # FT_DATA /* (vehicle) network data */

        # TODO make more compact, dry,
        # dict of queues
        self.queues = {
            GryphonProtocolFT.FT_CMD: self.cmd_q,
            GryphonProtocolFT.FT_RESP: self.resp_q,
            GryphonProtocolFT.FT_EVENT: self.event_q,
            GryphonProtocolFT.FT_MISC: self.misc_q,
            GryphonProtocolFT.FT_TEXT: self.text_q,
            GryphonProtocolFT.FT_SIG: self.sig_q,
            GryphonProtocolFT.FT_DATA: self.data_q,
        }

        # TODO
        # self.rx_q = Queue.Queue()  # FT_DATA /* (vehicle) network data */
        # self.tx_q = Queue.Queue()  # FT_DATA /* (vehicle) network data */
        # self.usdt_rx_q = Queue.Queue()  # FT_DATA /* (vehicle) network data */

        # start thread
        self.sock = sock
        self.timeout = timeout
        self.thr1_kill_event = threading.Event()
        self.thr1_kill_event.clear()
        self.thr1 = threading.Thread(target=self._read_thread)
        self.thr1.start()

    def __del__(self):
        """del all queues, kill and join read thread
        """
        for thisq in self.queues:
            del thisq
        if self.thr1 is not None:
            if self.thr1.isAlive():
                self.thr1_kill_event.set()
                self.thr1.join()
                self.thr1 = None
        self.client_id = None

    def _padding_number(self, msg_len):
        """gryphon protocol padding

        Args:
            message length

        Post:
            number of return bytes is 4 minus len mod 4

        Returns:
            either 0,1,2, or 3
        """
        #
        # ----------------------------------------------------------------------
        # pylint: disable=no-self-use
        # ----------------------------------------------------------------------
        #
        padding = [0, 3, 2, 1]
        # print "padding {}".format(padding[(msg_len % 4)])
        return padding[(msg_len % 4)]

    def _read_some(self, amount_expected):
        """read thread. read msgs

        Args:
            amount_expected - number of bytes to read

        Returns:
            None on kill event
            data list

        Raises:
            TooManyLoops
        """
        amount_received = 0
        timeout_count = 0
        readlen = amount_expected
        datar = []
        stop = self.thr1_kill_event.is_set()
        while amount_received < amount_expected and not stop:
            ready = select.select([self.sock], [], [], self.timeout)
            if ready[0]:
                # read header
                datar += self.sock.recv(readlen)
                amount_received += len(datar)
                readlen -= amount_received
                # print >>sys.stderr, '%s read total_recv=%d total_exp=%d' % (kind_str, amount_received, amount_expected)
            else:
                timeout_count += 1
                if timeout_count >= GryphonReadThread.MAX_RETRY_LOOPS:
                    # print "_read_thread() error timeout"
                    # for now, just continue until we get expected amount
                    raise TooManyLoops(timeout_count)
            stop = self.thr1_kill_event.is_set()
        if stop:
            return None
        return datar

    def _read_thread(self):
        """read thread. read msgs, put in proper queue
        put general msgs in general q

        loops while not self.thr1_kill_event

        Args:
            None.

        Raises:
            None.
        """
        while not self.thr1_kill_event.is_set():
            try:
                datar = self._read_some(8)
            except TooManyLoops:
                # this is infinite read loop, so just set to None and continue
                datar = None

            if datar:
                # got entire header
                # determine what to do now
                reply = {"GCprotocol": {"framehdr": {}, "body": {}}}
                if sys.version_info[0] < 3:
                    reply["GCprotocol"]["framehdr"].update({self.SRC: ord(datar[0])})
                    reply["GCprotocol"]["framehdr"].update(
                        {self.SRCCHAN: ord(datar[1])}
                    )
                    reply["GCprotocol"]["framehdr"].update({self.DST: ord(datar[2])})
                    reply["GCprotocol"]["framehdr"].update(
                        {self.CLIENT_ID: ord(datar[3])}
                    )
                    reply["GCprotocol"]["framehdr"].update(
                        {self.DSTCHAN: ord(datar[3])}
                    )
                    reply["GCprotocol"]["framehdr"].update(
                        {self.LEN: (ord(datar[4]) * 256) + ord(datar[5])}
                    )
                    frametype = ord(datar[6])
                else:
                    reply["GCprotocol"]["framehdr"].update({self.SRC: datar[0]})
                    reply["GCprotocol"]["framehdr"].update({self.SRCCHAN: datar[1]})
                    reply["GCprotocol"]["framehdr"].update({self.DST: datar[2]})
                    reply["GCprotocol"]["framehdr"].update({self.CLIENT_ID: datar[3]})
                    reply["GCprotocol"]["framehdr"].update({self.DSTCHAN: datar[3]})
                    reply["GCprotocol"]["framehdr"].update(
                        {self.LEN: (datar[4] * 256) + datar[5]}
                    )
                    frametype = datar[6]
                reply["GCprotocol"]["framehdr"].update({self.FRAMETYPE: frametype})

                # 2nd read
                # TODO why does FT_DATA have be to hacked?
                if not self.thr1_kill_event.is_set():
                    if frametype == GryphonProtocolFT.FT_DATA:
                        new_padding = reply["GCprotocol"]["framehdr"][self.LEN]
                        new_padding += self._padding_number(
                            reply["GCprotocol"]["framehdr"][self.LEN]
                        )
                        try:
                            datar2 = self._read_some(new_padding)
                        except TooManyLoops:
                            # the rest of the data is not coming
                            # TODO log the error
                            datar2 = None
                        # print "DEBUG---------------putting type {} into queues".format(reply[self.FRAMETYPE])
                    elif frametype == GryphonProtocolFT.FT_RESP:
                        new_padding = reply["GCprotocol"]["framehdr"][self.LEN]
                        new_padding += self._padding_number(
                            reply["GCprotocol"]["framehdr"][self.LEN]
                        )
                        try:
                            datar2 = self._read_some(new_padding)
                        except TooManyLoops:
                            # the rest of the data is not coming
                            # TODO log the error
                            datar2 = None
                    else:
                        # TODO try padding for all received msgs!
                        new_padding = reply["GCprotocol"]["framehdr"][self.LEN]
                        new_padding += self._padding_number(
                            reply["GCprotocol"]["framehdr"][self.LEN]
                        )
                        try:
                            datar2 = self._read_some(new_padding)
                        except TooManyLoops:
                            # the rest of the data is not coming
                            # TODO log the error
                            datar2 = None

                    reply["GCprotocol"]["body"].update({self.RAWDATA: datar2})
                    # temp disable
                    # self.general_q.put(reply)

                    # TODO
                    # if event
                    # reply[self.EVENT_ID] = ord(datar2[0])

                    # print "DEBUG -------------- type {}".format(frametype)
                    self.queues[frametype].put(reply)

    def is_alive(self):
        """return True if thread is alive
        """
        if self.thr1 is not None:
            return self.thr1.isAlive()
        return False

    def kill(self):
        """kill thread if alive, set the event and wait for join
        """
        if self.thr1 is not None:
            if self.thr1.isAlive():
                self.thr1_kill_event.set()
                self.thr1.join()
                self.thr1 = None

    def read_general_queue(self, timeout=None):
        """read msg from general queue

        Args:
            timeout

        Post:
            IF timeout is None
                returns item or Exception
            ELSE
                block until timeout or read is done

        Raises:
            IndexError on error accessing queue
        """
        if (timeout is None) or not isinstance(
            timeout, (six.integer_types, float)
        ):  # don't block
            try:
                return self.general_q.get()
            # except Queue.Empty:
            #     raise
            except IndexError:
                # TODO
                raise IndexError
        else:  # block read
            if self.general_q.qsize():  # get msg
                return self.general_q.get()
            try:  # block read
                timeoutf = float(timeout)
                return self.general_q.get(True, timeoutf)
            # except Queue.Empty:
            #     raise
            except IndexError:
                # TODO
                raise IndexError

    def read_type_queue(self, timeout=0, msgtype=GryphonProtocolFT.FT_RESP):
        """read msg from queue

        Args:
            block until read is done, otherwise return immediately
            msg type default is FT_RESP

        Returns:
            returnlist -
            item -
            None on timeout

        Raises:
            IndexError on error accessing queue
        """
        # TODO use timeout
        item = None
        if isinstance(msgtype, list):
            # TODO not implemented
            returnlist = []
            for item in msgtype:
                one_q = self.queues[item]
                try:
                    item = one_q.get(True, timeout)
                    if item is not None:
                        returnlist.append(item)
                    # print "DEBUG---------------pulled type {} from queues".format(item)
                # except Queue.Empty:
                #    print "DEBUG---------------queues empty exception"
                #    raise
                except IndexError:
                    # timeout
                    # print "DEBUG---------------queues other exception"
                    continue

            return returnlist
        one_q = self.queues[msgtype]
        try:
            item = one_q.get(True, timeout)
        # except Queue.Empty:
        #     raise
        except IndexError:
            # TODO
            raise IndexError
        return item

    def read_type_queue_nonblock(self, msgtype=GryphonProtocolFT.FT_RESP):
        """read msg from queue

        Args:
            msgtype - type of queue
        Returns:
            return msg, otherwise return immediately
            msg type default is FT_RESP

        Raises:
            IndexError on error accessing queue
        """
        # TODO use timeout
        if isinstance(msgtype, list):
            returnlist = []
            for item in msgtype:
                one_q = self.queues[item]
                try:
                    item = one_q.get_nonblock()
                    # print "DEBUG---------------pulled type {} from queues".format(item)
                except IndexError:
                    # print "DEBUG---------------queues other exception"
                    continue
                else:
                    returnlist.append(item)

            return returnlist
        one_q = self.queues[msgtype]
        try:
            return one_q.get_nonblock()
        except IndexError:
            # TODO
            raise IndexError


class Gryphon(GryphonProtocolDefines):
    """Gryphon

      Usage:
        ip = "10.94.44.185"
        try:
            gryph = dg_gryphon_protocol.Gryphon(ip)
        except socket.timeout:
            six.print_("socket.timeout: cannot connect to %s" % ip)
            return
        except:
            six.print_("unknown exception")
            return
        gryph.connect_to_server()
        client_id = gryph.CMD_SERVER_REG()
        configarray = gryph.CMD_GET_CONFIG()

        Attributes:
            self.product - BEACON or Gryphon
            self.password -
            self.client_id - client id
            self.src_type - client, this is client program
            self.last_returned_status - last status
            self.get_config - config
            self.cmd_context - rotating current context, 1 <= x <= 0xFF
            self.timeout - socket read timeout
            self.sock - socket
            self.ip - IP address
            self.port - port
            self.tx_loopback_channels - list of channels indicating tx loopback
            self.sock - socket
            self.read_thread - read thread

    """

    #
    # ----------------------------------------------------------------------
    # pylint: disable=too-many-ancestors
    # pylint: disable=invalid-name
    # pylint: disable=too-many-instance-attributes
    # pylint: disable=no-self-use
    # pylint: disable=too-many-public-methods
    # ----------------------------------------------------------------------
    #
    MAX_RETRY_LOOPS = 5
    SOCKET_TIMEOUT = 0.2

    def __init__(self, ip="localhost", port=7000, product="BEACON"):
        """init

        Args:
            ip address, port, product

        Returns:
            None on connection error

        Raises:
            socket.timeout on connection timeout
        """
        #
        # ----------------------------------------------------------------------
        # pylint: disable=global-statement
        # ----------------------------------------------------------------------
        #
        global GRYPHON_THREADED_CLIENT
        self.product = product
        self.password = None
        if self.product == "BEACON":
            self.password = "dgbeacon"
        else:
            self.password = "dggryphon"
        self.client_id = None
        self.src_type = GryphonProtocolSD.SD_CLIENT
        self.last_returned_status = None
        self.get_config = {}
        self.cmd_context = 1
        self.timeout = Gryphon.SOCKET_TIMEOUT
        self.sock = None
        self.ip = ip
        self.port = port
        self.tx_loopback_channels = []  # list of channels indicating tx loopback
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.read_thread = None
        # Bind the socket to the port
        server_address = (self.ip, self.port)
        self.sock.settimeout(self.SOCKET_TIMEOUT)

        try:
            self.sock.connect(server_address)
        except socket.timeout:
            self.sock.settimeout(None)
            self.sock.close()
            self.sock = None
            raise socket.timeout
        else:
            self.sock.settimeout(None)

        self.sock.setblocking(0)  # no blocking on recv, use select()

        # start read thread
        self.read_thread = GryphonReadThread(self.sock, self.timeout)
        GRYPHON_THREADED_CLIENT = self.read_thread

        """
        self.event_coll = collections.deque()
        self.resp_coll = collections.deque()
        self.misc_coll = collections.deque()
        self.text_coll = collections.deque()
        self.sig_coll = collections.deque()
        self.usdt_rx_coll = collections.deque()
        self.rx_coll = collections.deque()
        self.tx_coll = collections.deque()
        """

    def __del__(self):
        """delete
            Post:
                thread is dead
                socket is closed
        """
        if self.read_thread is not None:
            self.read_thread.kill()
            self.read_thread = None
        if self.sock is not None:
            self.sock.close()
            self.sock = None

    def __enter__(self):
        """this is used as: with Gryphon as gryph:
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """this is used as: with Gryphon as gryph:
        """

    def _padding(self, msg_len):
        """gryphon protocol padding

        Args:
            message length

        Returns:
            an array containing either 0,1,2, or 3 padding bytes, either
            [] for mod4 = 0
            [0, 0, 0] for mod4 = 1
            [0, 0] for mod4 = 2
            [0] for mod4 = 3
        """
        padding = [[], [0, 0, 0], [0, 0], [0]]
        # print "padding {}".format(padding[(msg_len % 4)])
        return padding[(msg_len % 4)]

    def is_overflow(self, msgtype=GryphonProtocolFT.FT_RESP):
        """return True if overflow

        Args:
            msgtype - queue type

        Returns:
            True if queue overflow
        """
        return self.read_thread.queues[msgtype].is_overflow()

    def read_event(self, chan=1):
        """read event

        Args:
            chan

        Returns:
            event

        Raises:
            None.
        """
        #
        # ----------------------------------------------------------------------
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        # pylint: disable=bare-except
        # ----------------------------------------------------------------------
        #
        # first check queue, if in queue, return it, otherwise read it
        #
        # ----------------------------------------------------------------------
        # unused-argument
        # TODO unused variable here
        # ----------------------------------------------------------------------
        _unused_param = chan
        _unused_param = _unused_param

        reply = self.read_thread.read_type_queue(
            timeout=0.25, msgtype=GryphonProtocolFT.FT_EVENT
        )
        return reply

    def _read_text(self, timeout=0.25):
        """read text
        Args:
            request command

        Returns:
            true no success, false on error

        Raises:
            None.
        """
        #
        # ----------------------------------------------------------------------
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        # ----------------------------------------------------------------------
        #
        # TODO implement a timeout or loop count
        # header read
        reply_dict = self.read_thread.read_type_queue(
            timeout=timeout, msgtype=GryphonProtocolFT.FT_TEXT
        )

        # data
        if reply_dict is False:
            return {"response_return_code": False}
        if isinstance(reply_dict, dict):
            reply_dict.update({"response_return_code": GryphonProtocolResp.RESP_OK})
        return reply_dict

    def _read_resp_func_from_lin(self, cmd, datar, reply, dst=GryphonProtocolSD.SD_LIN):
        """read response from lin
        """
        # TODO 20190108 left off HERE
        #
        # ----------------------------------------------------------------------
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        # ----------------------------------------------------------------------
        #
        # ----------------------------------------------------------------------
        # unused-argument
        # TODO unused variable here
        # ----------------------------------------------------------------------
        _unused_param = reply
        _unused_param = _unused_param

        if cmd == self.BCMD_LDF_LIST and dst == self.SD_LIN:
            ldf_dict = {}
            ldf_dict["number"] = ord(datar[8])
            ldf_dict["remaining"] = (ord(datar[10]) * 256) + ord(datar[11])
            ldf_dict["list"] = []
            start = 12
            for i in range(0, ldf_dict["number"]):
                ldf_list = {}
                end = start + 32
                ldf_list["name"] = "".join(datar[start:end])
                # split the string at the first null char
                if "\x00" in ldf_list["name"]:
                    ldf_list["name"] = ldf_list["name"].split("\x00")[0]
                start += 32
                end = start + 80
                ldf_list["description"] = "".join(datar[start:end])
                if "\x00" in ldf_list["description"]:
                    ldf_list["description"] = ldf_list["description"].split("\x00")[0]
                ldf_dict["list"].append(ldf_list)
                start += 80
                # print "NAME {} DESC {}".format(ldf_list['name'], ldf_list['description'])
                del ldf_list
            return ldf_dict
        if cmd == self.BCMD_GET_LDF_INFO and dst == self.SD_LIN:
            ldf_dict = {}
            ldf_dict["protocol"] = "".join(datar[0 + 8 : 16 + 8]).split("\x00")[0]
            ldf_dict["language"] = "".join(datar[16 + 8 : 32 + 8]).split("\x00")[0]
            # ldf_dict['bitrate'] = (ord(datar[32 + 8 + 0]) * 1) + (ord(datar[32 + 8 + 1]) * 256) + (ord(datar[32 + 8 + 2]) * 512) + (ord(datar[32 + 8 + 3]) * 1024)
            ldf_dict["bitrate"] = (
                (ord(datar[32 + 8 + 0]) * 1024)
                + (ord(datar[32 + 8 + 1]) * 512)
                + (ord(datar[32 + 8 + 2]) * 256)
                + (ord(datar[32 + 8 + 3]) * 1)
            )
            return ldf_dict
        if cmd == self.BCMD_GET_NODE_NAMES and dst == self.SD_LIN:
            ldf_array = []
            ind = 10
            number = listntohs(datar[8:ind])
            nodes = "".join(datar[ind:]).split("\x00")
            # print "-------------------------------number={} nodes={} ".format(number, nodes)
            for i in range(0, number):
                ldf_array.append(nodes[i])

            return ldf_array
        if cmd == self.BCMD_GET_NODE_SIGNALS and dst == self.SD_LIN:
            ldf_array = []
            ind = 10
            number = listntohs(datar[8:ind])
            nodes = "".join(datar[ind:]).split("\x00")
            for i in range(0, number):
                ldf_array.append(nodes[i])
            return ldf_array
        if cmd == self.BCMD_GET_FRAMES and dst == self.SD_LIN:
            ldf_array = []
            ind = 8
            number = listntohs(datar[ind : ind + 2])
            ind += 2
            for i in range(0, number):
                ldf_dict = {}
                ldf_dict["id"] = ord(datar[ind])
                ind += 1
                ldf_dict["name"] = "".join(datar[ind:]).split("\x00")[0]
                ind += len(ldf_dict["name"]) + 1
                ldf_array.append(ldf_dict)
            return ldf_array
        if cmd == self.BCMD_GET_FRAME_INFO and dst == self.SD_LIN:
            ldf_dict = {}
            ind = 8
            ldf_dict["databytes"] = ord(datar[ind])
            ind += 1
            rest = "".join(datar[ind:]).split("\x00")
            ldf_dict["publisher"] = rest[0]
            num_signals = ord(rest[1][0])
            ldf_dict["num_signals"] = num_signals
            publen = len(ldf_dict["publisher"])
            ind += 1 + publen + 1
            # re-split the data
            rest = "".join(datar[ind:]).split("\x00")
            ldf_dict["signals"] = rest[:num_signals]
            return ldf_dict
        if cmd == self.BCMD_GET_SIGNAL_INFO and dst == self.SD_LIN:
            ldf_dict = {}
            ind = 8
            ldf_dict["offset"] = ord(datar[ind])
            ind += 1
            ldf_dict["length"] = ord(datar[ind])
            ind += 1
            ldf_dict["signal_encoding_name"] = "".join(datar[ind:]).split("\x00")[0]
            return ldf_dict
        if cmd == self.BCMD_GET_SIGNAL_DETAIL and dst == self.SD_LIN:
            ldf_dict = {}
            ind = 8
            ldf_dict["offset"] = ord(
                datar[ind]
            )  # offset in bits, bit 0 is MSB of the data byte, bit 7 is LSB of data byte
            ind += 1
            ldf_dict["length"] = ord(datar[ind])  # length of signal in bits
            ind += 1
            number = listntohs(datar[ind : ind + 2])
            ldf_dict["number"] = number
            ind += 2
            ldf_dict["encodings"] = []
            for i in range(0, number):
                encoding_dict = {}
                # no no. This etype is 12-bytes long. always.
                encoding_dict["etype"] = "".join(datar[ind : ind + 12]).split("\x00")[0]
                ind += 12
                value = listntohs(datar[ind : ind + 2])
                ind += 2
                if encoding_dict["etype"] == "logical":
                    # 2-bytes and a var string
                    encoding_dict["value"] = value
                    encoding_dict["string"] = "".join(datar[ind:]).split("\x00")[0]
                    ind += len(encoding_dict["string"]) + 1
                elif encoding_dict["etype"] == "physical":
                    # 2-bytes, 2-bytes,  three var strings
                    encoding_dict["min"] = value
                    encoding_dict["max"] = listntohs(datar[ind : ind + 2])
                    ind += 2
                    rest = "".join(datar[ind:]).split("\x00")
                    encoding_dict["scale"] = rest[0]
                    encoding_dict["offset"] = rest[1]
                    encoding_dict["units"] = rest[2]
                    ind += len(rest[0]) + 1 + len(rest[1]) + 1 + len(rest[2]) + 1
                elif encoding_dict["etype"] == "bcd":
                    # 2-bytes
                    # nothing else
                    encoding_dict["value"] = value
                elif encoding_dict["etype"] == "ascii":
                    # 2-bytes
                    # nothing else
                    encoding_dict["value"] = value
                ldf_dict["encodings"].append(encoding_dict)
            return ldf_dict
        if cmd == self.BCMD_GET_ENCODING_INFO and dst == self.SD_LIN:
            ldf_dict = {}
            ind = 8
            number = listntohs(datar[ind : ind + 2])
            ldf_dict["number_encodings"] = number
            ind += 2
            ldf_dict["encodings"] = []
            for i in range(0, number):
                encoding_dict = {}
                # no no. This etype is 12-bytes long. always.
                encoding_dict["etype"] = "".join(datar[ind : ind + 12]).split("\x00")[0]
                ind += 12
                value = listntohs(datar[ind : ind + 2])
                ind += 2
                if encoding_dict["etype"] == "logical":
                    # 2-bytes and a var string
                    encoding_dict["value"] = value
                    encoding_dict["string"] = "".join(datar[ind:]).split("\x00")[0]
                    ind += len(encoding_dict["string"]) + 1
                elif encoding_dict["etype"] == "physical":
                    # 2-bytes, 2-bytes,  three var strings
                    encoding_dict["min"] = value
                    encoding_dict["max"] = listntohs(datar[ind : ind + 2])
                    ind += 2
                    rest = "".join(datar[ind:]).split("\x00")
                    encoding_dict["scale"] = rest[0]
                    encoding_dict["offset"] = rest[1]
                    encoding_dict["units"] = rest[2]
                    ind += len(rest[0]) + 1 + len(rest[1]) + 1 + len(rest[2]) + 1
                elif encoding_dict["etype"] == "bcd":
                    # 2-bytes
                    # nothing else
                    encoding_dict["value"] = value
                elif encoding_dict["etype"] == "ascii":
                    # 2-bytes
                    # nothing else
                    encoding_dict["value"] = value

                ldf_dict["encodings"].append(encoding_dict)
            return ldf_dict
        if cmd == self.BCMD_GET_SCHEDULES and dst == self.SD_LIN:
            ldf_array = []
            ind = 8
            number = listntohs(datar[ind : ind + 2])
            ind += 2
            rest = "".join(datar[ind:]).split("\x00")
            for i in range(0, number):
                ldf_array.append(rest[i])
            return ldf_array
        if cmd == self.BCMD_RESTORE_SESSION and dst == self.SD_LIN:
            ldf_file = ""
            start = 8
            end = start + 32
            ldf_file = "".join(datar[start:end]).split("\x00")[0]
            return ldf_file
        if cmd == self.BCMD_CNVT_GET_VALUES and dst == self.SD_CNVT:
            ldf_array = []
            ind = 8
            number = ord(datar[ind])
            ind += 1
            for i in range(0, number):
                sig_array = {}
                flags = ord(datar[ind])
                # print "0 ind {} flags {}".format(ind, flags)
                ind += 1
                sig_array["flags"] = flags
                if flags & 0x01 == 0x01:
                    # float TODO
                    number = listntohl(datar[ind : ind + 4])
                    sig_array["float"] = number
                    ind += 4
                if flags & 0x02 == 0x02:
                    # int
                    number = listntohl(datar[ind : ind + 4])
                    ind += 4
                    sig_array["int"] = number
                if flags & 0x04 == 0x04:
                    # string
                    string1 = "".join(datar[ind:]).split("\x00")[0]
                    ind += len(string1) + 1
                    sig_array["string"] = string1
                ldf_array.append(sig_array)
                del sig_array

            return ldf_array
        # TODO raise exception on unknown command
        return self.last_returned_status

    def _read_resp_func(self, cmd, dst=GryphonProtocolSD.SD_SERVER):
        """read response
        Args:
            request command

        Returns:
            now returns dict {}

        Raises:
            IndexError on queue read
        """
        #
        # ----------------------------------------------------------------------
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        # ----------------------------------------------------------------------
        #
        # TODO implement a timeout or loop count
        # header read
        reply = None
        try:
            reply = self.read_thread.read_type_queue(
                timeout=2.25, msgtype=GryphonProtocolFT.FT_RESP
            )
        except IndexError:
            # TODO
            raise IndexError

        # data
        if (reply is False) or (reply is None):
            return {"response_return_code": False}

        datar = reply["GCprotocol"]["body"][self.RAWDATA]
        if sys.version_info[0] < 3:
            reply["GCprotocol"]["body"]["cmd"] = ord(datar[0])
            # six.print_("====reply {}".format(reply))
            self.last_returned_status = (
                (ord(datar[4]) * 1024)
                + (ord(datar[5]) * 512)
                + (ord(datar[6]) * 256)
                + ord(datar[7])
            )
            reply["GCprotocol"]["body"]["status"] = reply[
                "response_return_code"
            ] = self.last_returned_status

            if reply["GCprotocol"]["body"]["cmd"] != cmd:
                return {"response_return_code": self.last_returned_status}
            reply["GCprotocol"]["body"]["context"] = ord(datar[1])

            if self.last_returned_status != 0:
                # TODO remove, debugging only
                six.print_(
                    "==ERROR==status is not OK 0x%08x cmd %x"
                    % (self.last_returned_status, cmd)
                )
                return reply

            # six.print_("====cmd {}".format(cmd))
            if cmd == self.BCMD_SERVER_REG:
                self.client_id = ord(datar[8])

        else:

            reply["GCprotocol"]["body"]["cmd"] = datar[0]
            # six.print_("====reply {}".format(reply))
            self.last_returned_status = (
                (datar[4] * 1024) + (datar[5] * 512) + (datar[6] * 256) + datar[7]
            )
            reply["GCprotocol"]["body"]["status"] = reply[
                "response_return_code"
            ] = self.last_returned_status

            if reply["GCprotocol"]["body"]["cmd"] != cmd:
                return {"response_return_code": self.last_returned_status}
            reply["GCprotocol"]["body"]["context"] = datar[1]

            if self.last_returned_status != 0:
                # TODO remove, debugging only
                six.print_(
                    "==ERROR==status is not OK 0x%08x cmd %x"
                    % (self.last_returned_status, cmd)
                )
                return reply

            # six.print_("====cmd {}".format(cmd))
            if cmd == self.BCMD_SERVER_REG:
                self.client_id = datar[8]

        # _______________________________________________________________________________
        # _______________________________________________________________________________
        # _______________________________________________________________________________
        # TODO 20190103 HERE convert to GCprotocol
        # _______________________________________________________________________________
        # _______________________________________________________________________________
        # _______________________________________________________________________________
        return reply

    def _wait_and_read_rx(
        self, frametype=GryphonProtocolFT.FT_DATA, hdr=None, data=None, timeout=0.05
    ):
        """wait for rx data
        Args:
            hdr - not used yet
            data - not used yet
            timeout - max time to wait for rx

        Pre:
            None.

        Post:


        Returns:
            dict success, None on error

        Raises:
            None.
        """
        # done 20190103
        #
        # ----------------------------------------------------------------------
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        # TODO unused variable here
        # pylint: disable=unused-argument
        # ----------------------------------------------------------------------
        #
        # TODO TODO implement a timeout or loop count
        reply = self.read_thread.read_type_queue(timeout=timeout, msgtype=frametype)

        # TODO implement wait for hdr and data
        if isinstance(reply, dict):
            reply.update({"response_return_code": GryphonProtocolResp.RESP_OK})
        return reply

    def _wait_and_read_event(self, srcchan=None, event=None):
        """wait for event
        Args:
            request command

        Pre:
            None.

        Post:


        Returns:
            true no success, false on error

        Raises:
            None.
        """
        #
        # ----------------------------------------------------------------------
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        # ----------------------------------------------------------------------
        #
        # TODO implement a timeout or loop count
        # header read
        reply = []
        while True:
            reply = self.read_thread.read_type_queue(
                timeout=0.25, msgtype=GryphonProtocolFT.FT_EVENT
            )
            datar = reply[self.DATASTR]

            if datar is None:
                # print "=========================================================() error datar 2"
                # TODO ?
                pass

            if srcchan is not None:
                if srcchan != reply[self.SRCCHAN]:
                    # print "=========================================================WARNING read reply got other chan, exp {} act {}".format(srcchan, reply[self.SRCCHAN])
                    # TODO ?
                    pass

            event_id = ord(datar[0])
            if event is not None:
                if event_id is not None:
                    if event_id != event:
                        # print "=========================================================WARNING got wrong event {} {}".format(event_id, datar)
                        continue

        # ---- got event for the requested channel
        # data

        return datar[8 : 8 + 12]

    def _build_and_send_command(
        self, dst, dstchan, cmd, data=None, unusual_length=None, src=None, srcchan=None
    ):
        #
        # ----------------------------------------------------------------------
        # pylint: disable=too-many-arguments
        # ----------------------------------------------------------------------
        #
        """holds all of the duplicate code used in the command methods

        Args:
            dst
            dstchan
            cmd
            optional data
            optional unusual_length
            optional src
            optional srcchan

        Pre:
            CMD_SERVER_REG()

        Post:
            BEACON has command
            BEACON sent response

        Returns:
            response message

        Raises:
            None.
        """
        # default to client_id
        if srcchan is None:
            srcchan = self.client_id
        if src is None:
            src = self.src_type

        # need the correct client_id, got it!
        # get all attributes of the class
        cmds = dir(GryphonProtocolCommands)
        # filter out all of the __x__ attributes
        cmds[:] = [x for x in cmds if "__" not in x]

        cmds2 = []
        # get the actual values of all of the commands, using the attribute names
        cmds2.extend([getattr(GryphonProtocolCommands, x) for x in cmds])

        # print "cmd={} {}".format(cmd, cmds2)

        if cmd not in cmds2:
            # print "ERROR cmd={} not in {}".format(cmd, cmds2)
            return False

        message = bytearray()
        message.extend([src, srcchan, dst, dstchan])
        message.extend([0, 0, self.FT_CMD, 0])
        # command
        message.extend([cmd, self.cmd_context, 0, 0])
        self.cmd_context += 1
        if self.cmd_context >= 256:
            self.cmd_context = 1

        if data is not None:
            message.extend(data)
        message.extend(self._padding(len(message)))

        if unusual_length is not None:
            msg_len_full = unusual_length
            # print "unlen {}".format(msg_len_full)
        else:
            msg_len_full = len(message) - 8

            # print "len {}".format(msg_len_full)

        if msg_len_full <= 255 - 8:
            message[4] = 0
            message[5] = msg_len_full
        else:
            # TODO make this work for message larger than 255 bytes!
            message[4] = (msg_len_full & 0xFF00) >> 8
            message[5] = msg_len_full & 0x00FF

        # print message[4]
        # print message[5]

        self.sock.sendall(message)

        # this now returns RESP_* on error, a list on success
        return self._read_resp_func(cmd, dst)

    def _build_and_send_text(self, dst, dstchan, text=None):
        #
        # ----------------------------------------------------------------------
        # pylint: disable=too-many-arguments
        # ----------------------------------------------------------------------
        #
        """send FT_TEXT

        Args:
            dst
            dstchan
            text

        Pre:
            CMD_SERVER_REG()

        Post:
            BEACON has message

        Returns:
            None.

        Raises:
            None.
        """
        message = bytearray()
        message.extend([self.src_type, self.client_id, dst, dstchan])
        message.extend([0, 0, self.FT_TEXT, 0])

        if text is not None:
            message.extend(text)
        message.extend(self._padding(len(message)))

        msg_len_full = len(message) - 8

        if msg_len_full <= 255 - 8:
            message[4] = 0
            message[5] = msg_len_full
        else:
            # TODO make this work for message larger than 255 bytes!
            message[4] = (msg_len_full & 0xFF00) >> 8
            message[5] = msg_len_full & 0x00FF

        self.sock.sendall(message)

    def _build_and_send_data(
        self,
        dst,
        dstchan,
        data=None,
        src=None,
        srcchan=None,
        fttype=GryphonProtocolFT.FT_DATA,
    ):
        #
        # ----------------------------------------------------------------------
        # pylint: disable=too-many-arguments
        # ----------------------------------------------------------------------
        #
        """send FT_TEXT (or FT_MISC)

        Args:
            dst
            dstchan
            text
            src optional, default is SD_CLIENT
            srcchan optional, default is client_id
            fttype optional, default is FT_DATA

        Pre:
            CMD_SERVER_REG()

        Post:
            BEACON has message

        Returns:
            None.

        Raises:
            None.
        """
        if srcchan is None:
            srcchan = self.client_id
        if src is None:
            src = self.src_type

        message = bytearray()
        message.extend([src, srcchan, dst, dstchan])
        message.extend([0, 0, fttype, 0])

        if data is not None:
            message.extend(data)

        # this is unusual. with the commands, the len includes the padding
        msg_len_full = len(message) - 8

        message.extend(self._padding(len(message)))

        if msg_len_full <= 255 - 8:
            message[4] = 0
            message[5] = msg_len_full
        else:
            # TODO make this work for message larger than 255 bytes!
            message[4] = (msg_len_full & 0xFF00) >> 8
            message[5] = msg_len_full & 0x00FF

        self.sock.sendall(message)

    def kill(self):
        """kill
        """
        if self.read_thread is not None:
            self.read_thread.kill()
            self.read_thread = None

    def CMD_SERVER_REG(
        self, username="root", password=None, src_type=GryphonProtocolSD.SD_CLIENT
    ):
        """register with server, the first command

        Args:
            user, password

        Pre:
            None.

        Post:
            client is registered and has client id, or error is returned

        Returns:
            A dictionary containing "client_id", "response_return_code" as one
            of the GryphonProtocolResp RESP_ codes.
            Also return "GCprotocol" containing entire GCprotocol message bytes.

        Raises:
            None.
        """
        # done 20190103
        #
        # ----------------------------------------------------------------------
        # TODO unused variable here
        # pylint: disable=unused-argument
        # ----------------------------------------------------------------------
        #

        # workaround for default method argument default to self variable
        if password is None:
            password = self.password

        self.src_type = src_type
        message = bytearray()
        message.extend([src_type, 0, self.SD_SERVER, 0])
        message.extend([0, 60 - 8, 1, 0])
        # command
        message.extend([self.BCMD_SERVER_REG, self.cmd_context, 0, 0])
        self.cmd_context += 1
        if self.cmd_context >= 256:
            self.cmd_context = 1

        # put username in next 16 bytes
        # put password in next 32 bytes
        if sys.version_info[0] < 3:
            message.extend(username[0:16])
            message.extend([0] * (16 - len(username)))
            message.extend(password[0:32])
        else:
            message.extend(bytes(username[0:16], encoding="ascii"))
            message.extend([0] * (16 - len(username)))
            message.extend(bytes(password[0:32], encoding="ascii"))

        msglen = len(message)
        message.extend([0] * (60 - msglen))
        message.extend(self._padding(len(message)))

        message[5] = len(message) - 8
        self.sock.sendall(message)
        reply = self._read_resp_func(message[8], self.SD_SERVER)
        reply["GCprotocol"]["body"].update({"data": {}})
        if sys.version_info[0] < 3:
            reply["GCprotocol"]["body"]["data"].update(
                {self.CLIENT_ID: ord(reply["GCprotocol"]["body"][self.RAWDATA][8])}
            )
            reply["GCprotocol"]["body"]["data"].update(
                {self.PRIV: ord(reply["GCprotocol"]["body"][self.RAWDATA][9])}
            )
        else:
            reply["GCprotocol"]["body"]["data"].update(
                {self.CLIENT_ID: reply["GCprotocol"]["body"][self.RAWDATA][8]}
            )
            reply["GCprotocol"]["body"]["data"].update(
                {self.PRIV: reply["GCprotocol"]["body"][self.RAWDATA][9]}
            )
        reply.update({"client_id": reply["GCprotocol"]["body"]["data"][self.CLIENT_ID]})
        return reply

    def CMD_SERVER_SET_OPT(self, opttype):
        """set opt

        Args:
            opttype

        Pre:
            CMD_SERVER_REG()

        Post:
            Sent CMD_SERVER_SET_OPT
            Got response or timeout

        Returns:
            response

        Raises:
            None.
        """
        databa = bytearray()
        databa.extend([opttype])
        return self._build_and_send_command(
            dst=self.SD_SERVER, dstchan=0, cmd=self.BCMD_SERVER_SET_OPT, data=databa
        )

    def CMD_GET_CONFIG(self):
        #
        # ----------------------------------------------------------------------
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-statements
        # ----------------------------------------------------------------------
        #
        """get config

        Args:
            none.

        Pre:
            CMD_SERVER_REG()

        Post:
            Sent CMD_GET_CONFIG
            Got response or timeout

        Returns:
            A dictionary reply["GCprotocol"]["body"]["data"] containing
            the config info, a "response_return_code" as one
            of the GryphonProtocolResp RESP_ codes.
            Also return "GCprotocol" containing entire GCprotocol message bytes.

        Raises:
            None.
        """
        # done 20190103
        #
        # ----------------------------------------------------------------------
        # pylint: disable=too-many-statements
        # ----------------------------------------------------------------------
        #
        reply = self._build_and_send_command(
            dst=self.SD_SERVER, dstchan=0, cmd=self.BCMD_GET_CONFIG
        )

        datar = reply["GCprotocol"]["body"][self.RAWDATA]
        # get config
        # device name
        start = 8
        end_in = start + 20
        # six.print_("-1--------------start{}--------end{}--------{}".format(start,end_in,datar[start:end_in]))
        if sys.version_info[0] < 3:
            datarc = datar[start:end_in]
        else:
            datarc = list(map(chr, datar[start:end_in]))

        end = datarc.index("\x00")  # find first null at end of C string

        if end < 0:
            return False
        # print "---name---%s" % ''.join(datar[8:end])
        self.get_config["device_name"] = "".join(datarc[:end])
        # device version
        start = end_in
        end_in = start + 8
        end = end_in
        # six.print_("-2--------------start{}--------end{}--------{}".format(start,end_in,datar[start:end_in]))
        if sys.version_info[0] < 3:
            datarc = datar[start:end_in]
        else:
            datarc = list(map(chr, datar[start:end_in]))

        self.get_config["device_version"] = "".join(datarc[:end])
        # print "---ver---%s" % self.get_config["device_version"]
        start = end_in
        end_in = start + 20

        if sys.version_info[0] < 3:
            datarc = datar[start:end_in]
        else:
            datarc = list(map(chr, datar[start:end_in]))

        end = datarc.index("\x00")  # find first null at end of C string

        if end < 0:
            return False
        self.get_config["serial_number"] = "".join(datarc[:end])
        start = end_in
        end_in = start + 1
        end = end_in
        # print "---n------%u" % ord(datar[start])
        if sys.version_info[0] < 3:
            self.get_config["nchannels"] = ord(datar[start])
        else:
            self.get_config["nchannels"] = datar[start]
        start = end_in
        # skip
        start += 11 + 4
        end_in = start + 1
        end = end_in

        # channels
        self.get_config["channels"] = {}
        for i in range(1, self.get_config["nchannels"] + 1):
            self.get_config["channels"][i] = {}

            # driver name as null-terminated ASCII string
            end_in = start + 20

            if sys.version_info[0] < 3:
                datarc = datar[start:end_in]
            else:
                datarc = list(map(chr, datar[start:end_in]))

            end = datarc.index("\x00")  # find first null at end of C string
            if end < 0:
                return False
            self.get_config["channels"][i]["driver_name"] = "".join(datarc[:end])
            start = end_in

            # driver version as null-terminated ASCII string
            end_in = start + 8

            if sys.version_info[0] < 3:
                datarc = datar[start:end_in]
            else:
                datarc = list(map(chr, datar[start:end_in]))

            end = datarc.index("\x00")  # find first null at end of C string

            if end < 0:
                return False
            self.get_config["channels"][i]["driver_version"] = "".join(datarc[:end])
            start = end_in
            # security string as ASCII string
            end_in = start + 16

            if sys.version_info[0] < 3:
                datarc = datar[start:end_in]
            else:
                datarc = list(map(chr, datar[start:end_in]))

            end = datarc.index("\x00")  # find first null at end of C string

            if end < 0:
                return False

            if sys.version_info[0] < 3:
                datarc = datar[start:end_in]
            else:
                datarc = list(map(chr, datar[start:end_in]))

            end = datarc.index("\x00")  # find first null at end of C string

            # six.print_("-3--------------start{}--------end{}--------{}----------{}".format(start,end_in,datar[start:end_in], datarc))
            self.get_config["channels"][i]["security_string"] = "".join(datarc[:end])
            # valid headers
            start = end_in
            end_in = start + 4
            if sys.version_info[0] < 3:
                header_lengths_bytes = (
                    (ord(datar[start]) * (256 * 3))
                    + (ord(datar[start + 1]) * (256 * 2))
                    + (ord(datar[start + 2]) * 256)
                    + (ord(datar[start + 3]))
                )
            else:
                header_lengths_bytes = (
                    (datar[start] * (256 * 3))
                    + (datar[start + 1] * (256 * 2))
                    + (datar[start + 2] * 256)
                    + (datar[start + 3])
                )

            self.get_config["channels"][i]["header_sizes"] = []
            for count, bit in enumerate(range(0, 32)):
                bitmask = 1 << bit
                if header_lengths_bytes & bitmask:
                    self.get_config["channels"][i]["header_sizes"].append(count)

            # max data len
            start = end_in
            end_in = start + 2
            if sys.version_info[0] < 3:
                self.get_config["channels"][i]["max_data_len"] = (
                    ord(datar[start]) * 256
                ) + (ord(datar[start + 1]))
            else:
                self.get_config["channels"][i]["max_data_len"] = (
                    datar[start] * 256
                ) + (datar[start + 1])
            # min data len
            start = end_in
            end_in = start + 2
            if sys.version_info[0] < 3:
                self.get_config["channels"][i]["min_data_len"] = (
                    ord(datar[start]) * 256
                ) + (ord(datar[start + 1]))
            else:
                self.get_config["channels"][i]["min_data_len"] = (
                    datar[start] * 256
                ) + (datar[start + 1])
            # hardware serial number as ASCII string
            start = end_in
            end_in = start + 20

            if sys.version_info[0] < 3:
                datarc = datar[start:end_in]
            else:
                datarc = list(map(chr, datar[start:end_in]))

            end = datarc.index("\x00")  # find first null at end of C string
            if end < 0:
                return False
            self.get_config["channels"][i]["serial_number"] = "".join(datarc[:end])

            # type
            start = end_in
            if sys.version_info[0] < 3:
                self.get_config["channels"][i]["type"] = ord(datar[start])
            else:
                self.get_config["channels"][i]["type"] = datar[start]
            # subtype
            start += 1
            if sys.version_info[0] < 3:
                self.get_config["channels"][i]["subtype"] = ord(datar[start])
            else:
                self.get_config["channels"][i]["subtype"] = datar[start]
            # number
            start += 1
            if sys.version_info[0] < 3:
                self.get_config["channels"][i]["number"] = ord(datar[start])
            else:
                self.get_config["channels"][i]["number"] = datar[start]
            # card slot
            start += 1
            if sys.version_info[0] < 3:
                self.get_config["channels"][i]["card_slot"] = ord(datar[start])
            else:
                self.get_config["channels"][i]["card_slot"] = datar[start]
            start += 1
            # max extra len
            if sys.version_info[0] < 3:
                self.get_config["channels"][i]["max_extra_len"] = (
                    ord(datar[start]) * 256
                ) + (ord(datar[start + 1]))
            else:
                self.get_config["channels"][i]["max_extra_len"] = (
                    datar[start] * 256
                ) + (datar[start + 1])
            start += 2
            # min extra len
            if sys.version_info[0] < 3:
                self.get_config["channels"][i]["min_extra_len"] = (
                    ord(datar[start]) * 256
                ) + (ord(datar[start + 1]))
            else:
                self.get_config["channels"][i]["min_extra_len"] = (
                    datar[start] * 256
                ) + (datar[start + 1])
            start += 2

        reply["GCprotocol"]["body"].update({"data": {}})
        reply["GCprotocol"]["body"]["data"].update(self.get_config)
        return reply

    def CMD_GENERIC(
        self,
        data_in,
        set_client_id=True,
        add_padding=True,
        set_context=True,
        set_length=True,
    ):
        #
        # ----------------------------------------------------------------------
        # pylint: disable=too-many-arguments
        # ----------------------------------------------------------------------
        #
        """generic command

        Args:
            gryphon protocol data in a bytearray, including the header
            set_client_id=True to change the client id to the data_in[1] value.
            add_padding=True to adjust the data_in padding.
            set_context=True to set the context byte to the next value.
            set_length=True to re-calculate and set the data length.

        Pre:
            None

        Post:
            this is special.

        Returns:
            array of bytes

        Raises:
            None.
        """
        if set_client_id:
            # set client id
            data_in[1] = self.client_id
        if set_context:
            # set the context
            if len(data_in) < 10:
                addsomelen = 10 - len(data_in)
                tmp1 = [0] * (addsomelen)
                data_in.extend(tmp1)
            data_in[9] = self.cmd_context
            self.cmd_context += 1
            if self.cmd_context >= 256:
                self.cmd_context = 1
        # TODO make this work for message larger than 255 bytes!
        if add_padding:
            # do the padding
            data_in.extend(self._padding(len(data_in)))
        if set_length:
            # warning, this needs to be done after add_padding
            # set the length
            data_in[5] = len(data_in) - 8
        self.sock.sendall(data_in)
        cmd = data_in[8]
        return self._read_resp_func(cmd, data_in[2])

    def CMD_GET_TIME(self):
        """get time

        Args:
            none.

        Pre:
            CMD_SERVER_REG()

        Post:
            Sent CMD_GET_TIME
            Got response or timeout

        Returns:
            A dictionary reply["GCprotocol"]["body"]["data"] containing
            the config info, a "response_return_code" as one
            of the GryphonProtocolResp RESP_ codes.
            Also return "GCprotocol" containing entire GCprotocol message bytes.

        Raises:
            None.
        """
        # done 20190103
        reply_dict = self._build_and_send_command(
            dst=self.SD_SERVER, dstchan=0, cmd=self.BCMD_GET_TIME
        )
        reply_dict["GCprotocol"]["body"].update({"data": {}})
        mytime = 0
        if sys.version_info[0] < 3:
            mytime += ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][8]) << 56
            mytime += ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][9]) << 48
            mytime += ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][10]) << 40
            mytime += ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][11]) << 32
            mytime += ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][12]) << 24
            mytime += ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][13]) << 16
            mytime += ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][14]) << 8
            mytime += ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][15]) << 0
        else:
            mytime += reply_dict["GCprotocol"]["body"][self.RAWDATA][8] << 56
            mytime += reply_dict["GCprotocol"]["body"][self.RAWDATA][9] << 48
            mytime += reply_dict["GCprotocol"]["body"][self.RAWDATA][10] << 40
            mytime += reply_dict["GCprotocol"]["body"][self.RAWDATA][11] << 32
            mytime += reply_dict["GCprotocol"]["body"][self.RAWDATA][12] << 24
            mytime += reply_dict["GCprotocol"]["body"][self.RAWDATA][13] << 16
            mytime += reply_dict["GCprotocol"]["body"][self.RAWDATA][14] << 8
            mytime += reply_dict["GCprotocol"]["body"][self.RAWDATA][15] << 0
        stime = int(mytime / 100000)
        ustime = (mytime % 100000) * 10
        pytime = str(datetime.datetime.fromtimestamp(stime)) + "." + str(ustime)
        reply_dict["GCprotocol"]["body"]["data"].update({"linuxtime": stime})
        reply_dict["GCprotocol"]["body"]["data"].update({"pytime": pytime})
        reply_dict["GCprotocol"]["body"]["data"].update({"microseconds": ustime})
        return reply_dict

    def CMD_SET_TIME(self, microseconds, linuxtime=None):
        """set time

        Args:
            microseconds - the new Gryphon timestamp
            linuxtime - optional system time, number of seconds since epoch

        Pre:
            CMD_SERVER_REG()

        Post:

        Returns:
            A dictionary reply["GCprotocol"]["body"]["data"] containing
            the config info, a "response_return_code" as one
            of the GryphonProtocolResp RESP_ codes.
            Also return "GCprotocol" containing entire GCprotocol message bytes.

        Raises:
            None.
        """
        # done 20190103
        timedata = [0] * 8  # init
        if linuxtime is None:
            # only set the Gryphon timestamp, get linux time from CMD_GET_TIME
            time_dict = self.CMD_GET_TIME()
            linuxtime = time_dict["GCprotocol"]["body"]["data"]["linuxtime"]

        linuxtime = linuxtime * 100000
        linuxtime += microseconds
        timedata[0] = (linuxtime & 0xFF00000000000000) >> 56
        timedata[1] = (linuxtime & 0x00FF000000000000) >> 48
        timedata[2] = (linuxtime & 0x0000FF0000000000) >> 40
        timedata[3] = (linuxtime & 0x000000FF00000000) >> 32
        timedata[4] = (linuxtime & 0x00000000FF000000) >> 24
        timedata[5] = (linuxtime & 0x0000000000FF0000) >> 16
        timedata[6] = (linuxtime & 0x000000000000FF00) >> 8
        timedata[7] = (linuxtime & 0x00000000000000FF) >> 0

        databa = bytearray()
        databa.extend(timedata)
        reply_dict = self._build_and_send_command(
            dst=self.SD_SERVER, dstchan=0, cmd=self.BCMD_SET_TIME, data=databa
        )
        return reply_dict

    def CMD_USDT_REGISTER_NON_LEGACY(
        self, chan, register_action=True, tx_options=None, rx_options=None, blocks=None
    ):
        """register USDT
        tx_options['echo_long'] - True or False, optional, default is False
        tx_options['padding'] - 0x00, 0xFF, or None, optional, default is None no padding
        tx_options['send_done_event'] - True or False, optional, default is False
        tx_options['echo_short'] - True or False, optional, default is False
        tx_options['send_rx_control_flow_event'] - True or False, optional, default is False
        rx_options['verify_and_send'] - True or False or None, optional, default is None
        rx_options['send_firstframe_event'] - True or False, optional, default is False
        rx_options['send_lastframe_event'] - True or False, optional, default is False
        rx_options['send_tx_control_flow_event'] - True or False, optional, default is False
        blocks[n]['number'] - number of IDs this block represents, default is 1
        blocks[n]['J1939_style_length'] - True or False, optional, default is False
        blocks[n]['USDT_request_id_29bits'] - True or False, optional, default is False
        blocks[n]['USDT_request_id_ext_addressing'] - True or False, optional, default is False
        blocks[n]['USDT_request_id'] - 0x0000 to 0x07FF AND'ed with 0xA000, or 0x00000000 to 0x1fffffff AND'ed with 0xA0000000
        blocks[n]['USDT_request_ext_address'] - 0x00 to 0xFF, needed if ext_addressing

        blocks[n]['USDT_response_id_29bits'] - True or False, optional, default is False
        blocks[n]['USDT_response_id_ext_addressing'] - True or False, optional, default is False
        blocks[n]['USDT_response_id'] - 0x0000 to 0x07FF AND'ed with 0xA000, or 0x00000000 to 0x1fffffff AND'ed with 0xA0000000
        blocks[n]['USDT_response_ext_address'] - 0x00 to 0xFF, needed if ext_addressing

        blocks[n]['UUDT_response_id_29bits'] - True or False, optional, default is False
        blocks[n]['UUDT_response_id_ext_addressing'] - True or False, optional, default is False
        blocks[n]['UUDT_response_id'] - 0x0000 to 0x07FF AND'ed with 0xA000, or 0x00000000 to 0x1fffffff AND'ed with 0xA0000000
        blocks[n]['UUDT_response_ext_address'] - 0x00 to 0xFF, needed if ext_addressing

        Args:
            none.

        Pre:
            CMD_SERVER_REG()
            1 <= chan <= n_channels
            chan is type CAN

        Post:

        Returns:
            dict

        Raises:
            ChannelNotValid(chan)
        """
        #
        # ----------------------------------------------------------------------
        # pylint: disable=too-many-arguments
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        # ----------------------------------------------------------------------
        #
        # done 20190103
        if chan == 0:
            raise self.ChannelNotValid(chan)

        databa = bytearray()
        register_action_value = 0
        if register_action:
            register_action_value = 1

        # register
        transmit_options = 0x00
        if tx_options:
            if "echo_long" in tx_options:
                if tx_options["echo_long"]:
                    transmit_options |= 0x01  # -------1
            if "padding" in tx_options:
                if tx_options["padding"] is None:
                    transmit_options |= 0x04  # -----10- no pad, default
                else:
                    if tx_options["padding"] == 0xFF:
                        transmit_options |= 0x02  # -----01- pad with 0xFF
                    else:
                        transmit_options |= 0x00  # -----00- pad with 0x00

            if "send_done_event" in tx_options:
                if tx_options["send_done_event"]:
                    transmit_options |= 0x08  # ----1---

            if "echo_short" in tx_options:
                if tx_options["echo_short"]:
                    transmit_options |= 0x10  # ---1----

            if "send_rx_control_flow_event" in tx_options:
                if tx_options["send_rx_control_flow_event"]:
                    transmit_options |= 0x20  # --1-----

        receive_options = 0x00
        if rx_options:
            if "verify_and_send" in rx_options:
                if rx_options["verify_and_send"]:
                    receive_options |= 0x01  # ------01
                else:
                    receive_options |= 0x02  # ------10

            if "send_firstframe_event" in rx_options:
                if rx_options["send_firstframe_event"]:
                    receive_options |= 0x04  # -----1--

            if "send_lastframe_event" in rx_options:
                if rx_options["send_lastframe_event"]:
                    receive_options |= 0x08  # ----1---

            if "send_tx_control_flow_event" in rx_options:
                if rx_options["send_tx_control_flow_event"]:
                    receive_options |= 0x20  # --1-----

        # add to databa
        databa.extend([register_action_value, transmit_options, receive_options, 0])

        if blocks:
            for block in blocks:
                number = 1
                if "number" in block:
                    number = block["number"]

                if "J1939_style_length" in block:
                    if block["J1939_style_length"]:
                        number |= 0x40000000

                n1 = (number & 0xFF000000) >> 24
                n2 = (number & 0x00FF0000) >> 16
                n3 = (number & 0x0000FF00) >> 8
                n4 = (number & 0x000000FF) >> 0

                databa.extend([n1, n2, n3, n4])

                # TODO add some 11-bit 29-bit error checking, raise exceptions
                usdt_req = 0x00000000
                if "USDT_request_id" in block:
                    usdt_req = block["USDT_request_id"]
                if "USDT_request_id_ext_addressing" in block:
                    if block["USDT_request_id_ext_addressing"]:
                        usdt_req |= 0x20000000
                if "USDT_request_id_29bits" in block:
                    if block["USDT_request_id_29bits"]:
                        usdt_req |= 0x80000000

                usdt_req1 = (usdt_req & 0xFF000000) >> 24
                usdt_req2 = (usdt_req & 0x00FF0000) >> 16
                usdt_req3 = (usdt_req & 0x0000FF00) >> 8
                usdt_req4 = (usdt_req & 0x000000FF) >> 0

                databa.extend([usdt_req1, usdt_req2, usdt_req3, usdt_req4])

                usdt_resp = 0x00000000
                if "USDT_response_id" in block:
                    usdt_resp = block["USDT_response_id"]
                if "USDT_response_id_ext_addressing" in block:
                    if block["USDT_response_id_ext_addressing"]:
                        usdt_resp |= 0x20000000
                if "USDT_response_id_29bits" in block:
                    if block["USDT_response_id_29bits"]:
                        usdt_resp |= 0x80000000

                usdt_resp1 = (usdt_resp & 0xFF000000) >> 24
                usdt_resp2 = (usdt_resp & 0x00FF0000) >> 16
                usdt_resp3 = (usdt_resp & 0x0000FF00) >> 8
                usdt_resp4 = (usdt_resp & 0x000000FF) >> 0

                databa.extend([usdt_resp1, usdt_resp2, usdt_resp3, usdt_resp4])

                uudt_resp = 0x00000000
                if "UUDT_response_id" in block:
                    uudt_resp = block["UUDT_response_id"]
                if "UUDT_response_id_ext_addressing" in block:
                    if block["UUDT_response_id_ext_addressing"]:
                        uudt_resp |= 0x20000000
                if "UUDT_response_id_29bits" in block:
                    if block["UUDT_response_id_29bits"]:
                        uudt_resp |= 0x80000000

                uudt_resp1 = (uudt_resp & 0xFF000000) >> 24
                uudt_resp2 = (uudt_resp & 0x00FF0000) >> 16
                uudt_resp3 = (uudt_resp & 0x0000FF00) >> 8
                uudt_resp4 = (uudt_resp & 0x000000FF) >> 0

                databa.extend([uudt_resp1, uudt_resp2, uudt_resp3, uudt_resp4])

                usdt_req_ext = 0
                if "USDT_request_ext_address" in block:
                    usdt_req_ext = block["USDT_request_ext_address"]
                usdt_req_ext = 0
                if "USDT_response_ext_address" in block:
                    usdt_req_ext = block["USDT_response_ext_address"]
                uudt_resp_ext = 0
                if "UUDT_response_ext_address" in block:
                    uudt_resp_ext = block["UUDT_response_ext_address"]
                databa.extend([usdt_req_ext, usdt_req_ext, uudt_resp_ext, 0])

        reply_dict = self._build_and_send_command(
            dst=self.SD_USDT, dstchan=chan, cmd=self.BCMD_USDT_REGISTER_NON, data=databa
        )
        return reply_dict

    def CMD_USDT_SET_STMIN_FC(self, chan, stmin):
        """set stmin flow control

        Args:
            1 <= chan <= n_channels
            value of the stmin fc, 0 to 127 msec

        Pre:
            CMD_SERVER_REG()
            CMD_USDT_REGISTER_NON_LEGACY()
            1 <= chan <= n_channels
            chan is type CAN

        Post:

        Returns:
            dict

        Raises:
            None.
        """
        # done 20190103
        if chan == 0:
            raise self.ChannelNotValid(chan)

        databa = bytearray()
        databa.extend([stmin])
        # TODO this is unusual, will not work with size=8
        reply_dict = self._build_and_send_command(
            dst=self.SD_USDT,
            dstchan=chan,
            cmd=self.BCMD_USDT_SET_STMIN_FC,
            data=databa,
            unusual_length=5,
        )
        return reply_dict

    def CMD_USDT_GET_STMIN_FC(self, chan):
        """get stmin flow control

        Args:
            1 <= chan <= n_channels

        Pre:
            CMD_SERVER_REG()
            CMD_USDT_REGISTER_NON_LEGACY()
            1 <= chan <= n_channels
            chan is type CAN

        Post:

        Returns:
            dict containing value of the stmin fc, 0 to 127 msec

        Raises:
            None.
        """
        # done 20190103
        if chan == 0:
            raise self.ChannelNotValid(chan)

        reply_dict = self._build_and_send_command(
            dst=self.SD_USDT, dstchan=chan, cmd=self.BCMD_USDT_GET_STMIN_FC, data=None
        )
        reply_dict["GCprotocol"]["body"].update({"data": {}})
        if sys.version_info[0] < 3:
            reply_dict["GCprotocol"]["body"]["data"].update(
                {"stmin": ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][8])}
            )
        else:
            reply_dict["GCprotocol"]["body"]["data"].update(
                {"stmin": reply_dict["GCprotocol"]["body"][self.RAWDATA][8]}
            )
        return reply_dict

    def CMD_USDT_SET_BSMAX_FC(self, chan, bsmax):
        """set bsmax flow control

        Args:
            1 <= chan <= n_channels
            value of the bsmax fc, 0 to 255 bytes

        Pre:
            CMD_SERVER_REG()
            CMD_USDT_REGISTER_NON_LEGACY()
            1 <= chan <= n_channels
            chan is type CAN

        Post:

        Returns:
            dict

        Raises:
            None.
        """
        # done 20190103
        if chan == 0:
            raise self.ChannelNotValid(chan)

        databa = bytearray()
        databa.extend([bsmax])
        # TODO this is unusual, will not work with size=8
        reply_dict = self._build_and_send_command(
            dst=self.SD_USDT,
            dstchan=chan,
            cmd=self.BCMD_USDT_SET_BSMAX_FC,
            data=databa,
            unusual_length=5,
        )
        return reply_dict

    def CMD_USDT_GET_BSMAX_FC(self, chan):
        """get bsmax flow control

        Args:
            1 <= chan <= n_channels

        Pre:
            CMD_SERVER_REG()
            CMD_USDT_REGISTER_NON_LEGACY()
            1 <= chan <= n_channels
            chan is type CAN

        Post:

        Returns:
            dict value of the bsmax fc, 0 to 255 bytes

        Raises:
            None.
        """
        # done 20190103
        if chan == 0:
            raise self.ChannelNotValid(chan)

        reply_dict = self._build_and_send_command(
            dst=self.SD_USDT, dstchan=chan, cmd=self.BCMD_USDT_GET_BSMAX_FC, data=None
        )
        reply_dict["GCprotocol"]["body"].update({"data": {}})
        if sys.version_info[0] < 3:
            reply_dict["GCprotocol"]["body"]["data"].update(
                {"bsmax": ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][8])}
            )
        else:
            reply_dict["GCprotocol"]["body"]["data"].update(
                {"bsmax": reply_dict["GCprotocol"]["body"][self.RAWDATA][8]}
            )
        return reply_dict

    def CMD_USDT_SET_STMIN_OVERRIDE(self, chan, stmin_override):
        """set stmin_override

        Args:
            1 <= chan <= n_channels
            value , 0 to 127 milliseconds

        Pre:
            CMD_SERVER_REG()
            CMD_USDT_REGISTER_NON_LEGACY()
            1 <= chan <= n_channels
            chan is type CAN

        Post:

        Returns:
            dict

        Raises:
            None.
        """
        # done 20190103
        if chan == 0:
            raise self.ChannelNotValid(chan)

        databa = bytearray()
        databa.extend([stmin_override])
        # TODO this is unusual, will not work with size=8
        reply_dict = self._build_and_send_command(
            dst=self.SD_USDT,
            dstchan=chan,
            cmd=self.BCMD_USDT_SET_STMIN_OVERRIDE,
            data=databa,
            unusual_length=5,
        )
        return reply_dict

    def CMD_USDT_GET_STMIN_OVERRIDE(self, chan):
        """get stmin override

        Args:
            1 <= chan <= n_channels

        Pre:
            CMD_SERVER_REG()
            CMD_USDT_REGISTER_NON_LEGACY()
            1 <= chan <= n_channels
            chan is type CAN

        Post:

        Returns:
            dict containing value, 0 to 127 msec

        Raises:
            None.
        """
        # done 20190103
        if chan == 0:
            raise self.ChannelNotValid(chan)

        reply_dict = self._build_and_send_command(
            dst=self.SD_USDT,
            dstchan=chan,
            cmd=self.BCMD_USDT_GET_STMIN_OVERRIDE,
            data=None,
        )
        reply_dict["GCprotocol"]["body"].update({"data": {}})
        if sys.version_info[0] < 3:
            reply_dict["GCprotocol"]["body"]["data"].update(
                {
                    "stmin_override": ord(
                        reply_dict["GCprotocol"]["body"][self.RAWDATA][8]
                    )
                }
            )
        else:
            reply_dict["GCprotocol"]["body"]["data"].update(
                {"stmin_override": reply_dict["GCprotocol"]["body"][self.RAWDATA][8]}
            )
        return reply_dict

    def CMD_USDT_ACTIVATE_STMIN_OVERRIDE(self, chan, activate=True):
        """actvate/deactivate stmin override

        Args:
            1 <= chan <= n_channels

        Pre:
            CMD_SERVER_REG()
            CMD_USDT_REGISTER_NON_LEGACY()
            1 <= chan <= n_channels
            chan is type CAN

        Post:

        Returns:
            dict

        Raises:
            None.
        """
        # done 20190103
        if chan == 0:
            raise self.ChannelNotValid(chan)

        databa = bytearray()
        if activate:
            databa.extend([1])
        else:
            databa.extend([0])
        # TODO this is unusual, will not work with size=8
        reply_dict = self._build_and_send_command(
            dst=self.SD_USDT,
            dstchan=chan,
            cmd=self.BCMD_USDT_ACTIVATE_STMIN_OVERRIDE,
            data=databa,
            unusual_length=5,
        )
        return reply_dict

    def CMD_USDT_SET_STMIN_MULT(self, chan, stmin_mult):
        """set stmin flow control

        Args:
            chan
            value of the stmin mult in floating point format

        Pre:
            CMD_SERVER_REG()
            CMD_USDT_REGISTER_NON_LEGACY()
            1 <= chan <= n_channels
            chan is type CAN

        Post:

        Returns:
            True on success, otherwise False

        Raises:
            None.
        """
        # done 20190103
        if chan == 0:
            raise self.ChannelNotValid(chan)
        databa = bytearray(
            struct.pack(">f", stmin_mult)
        )  # pack floating point number into bytearray
        # databa = bytearray([1])  # a test
        reply_dict = self._build_and_send_command(
            dst=self.SD_USDT,
            dstchan=chan,
            cmd=self.BCMD_USDT_SET_STMIN_MULT,
            data=databa,
        )
        return reply_dict

    def CMD_BCAST_ON(self):
        """set broadcast on

        Args:
            none.

        Pre:
            CMD_SERVER_REG()

        Post:

        Returns:
            A dictionary containing "response_return_code" as one
            of the GryphonProtocolResp RESP_ codes.
            Also return "GCprotocol" containing entire GCprotocol message bytes.

        Raises:
            None.
        """
        # done 20190103
        return self._build_and_send_command(
            dst=self.SD_SERVER, dstchan=0, cmd=self.BCMD_BCAST_ON
        )

    def CMD_BCAST_OFF(self):
        """set broadcast off

        Args:
            none.

        Pre:
            CMD_SERVER_REG()

        Post:

        Returns:
            A dictionary containing "response_return_code" as one
            of the GryphonProtocolResp RESP_ codes.
            Also return "GCprotocol" containing entire GCprotocol message bytes.

        Raises:
            None.
        """
        # done 20190103
        return self._build_and_send_command(
            dst=self.SD_SERVER, dstchan=0, cmd=self.BCMD_BCAST_OFF
        )

    class ChannelNotValid(Exception):
        """chan value cannot be 0
            Usage:
                raise Gryphon.ChannelNotValid(chan)
        """

        def __init__(self, arg1=None):
            self.arg1 = arg1
            super(Gryphon.ChannelNotValid, self).__init__(arg1)

    class IncorrectXMLConfigFilename(Exception):
        """chan value cannot be 0
            Usage:
                raise Gryphon.IncorrectXMLConfigFilename(filename)
        """

        def __init__(self, arg1=None):
            self.arg1 = arg1
            super(Gryphon.IncorrectXMLConfigFilename, self).__init__(arg1)

    class ValueNotInt(Exception):
        """value must be int or long
        """

        def __init__(self, arg1=None):
            self.arg1 = arg1
            super(Gryphon.ValueNotInt, self).__init__(arg1)

    class FlagsNotFound(Exception):
        """data_in does not contained necessary "flags" item
        """

        def __init__(self, arg1=None):
            self.arg1 = arg1
            super(Gryphon.FlagsNotFound, self).__init__(arg1)

    class FilterBlocksNotFound(Exception):
        """data_in does not contained necessary "filter_blocks" item
        """

        def __init__(self, arg1=None):
            self.arg1 = arg1
            super(Gryphon.FilterBlocksNotFound, self).__init__(arg1)

    class RespBlocksNotFound(Exception):
        """data_in does not contained necessary "response_blocks" item
        """

        def __init__(self, arg1=None):
            self.arg1 = arg1
            super(Gryphon.RespBlocksNotFound, self).__init__(arg1)

    class ActionNotValid(Exception):
        """action is not 0,1,2
            Usage:
                raise Gryphon.ActionNotValid(action)
        """

        def __init__(self, arg1=None):
            self.arg1 = arg1
            super(Gryphon.ActionNotValid, self).__init__(arg1)

    class TimeIntervalNotFound(Exception):
        """data_in does not contained necessary "time_interval" item
        """

        def __init__(self, arg1=None):
            self.arg1 = arg1
            super(Gryphon.TimeIntervalNotFound, self).__init__(arg1)

    class MsgCountNotFound(Exception):
        """data_in does not contained necessary "message_count" item
        """

        def __init__(self, arg1=None):
            self.arg1 = arg1
            super(Gryphon.MsgCountNotFound, self).__init__(arg1)

    class ByteOffsetNotFound(Exception):
        """data_in does not contained necessary "byte_offset" item
        """

        def __init__(self, arg1=None):
            self.arg1 = arg1
            super(Gryphon.ByteOffsetNotFound, self).__init__(arg1)

    class FrameHdrNotFound(Exception):
        """framehdr not found
        """

        def __init__(self, arg1=None):
            self.arg1 = arg1
            super(Gryphon.FrameHdrNotFound, self).__init__(arg1)

    class BodyNotFound(Exception):
        """framehdr not found
        """

        def __init__(self, arg1=None):
            self.arg1 = arg1
            super(Gryphon.BodyNotFound, self).__init__(arg1)

    class TextNotFound(Exception):
        """framehdr not found
        """

        def __init__(self, arg1=None):
            self.arg1 = arg1
            super(Gryphon.TextNotFound, self).__init__(arg1)

    class DataNotFound(Exception):
        """framehdr not found
        """

        def __init__(self, arg1=None):
            self.arg1 = arg1
            super(Gryphon.DataNotFound, self).__init__(arg1)

    class OperatorNotFound(Exception):
        """data_in["filter_blocks"][n] does not contained necessary "operator" item
        """

        def __init__(self, arg1=None):
            self.arg1 = arg1
            super(Gryphon.OperatorNotFound, self).__init__(arg1)

    class ValueNotInFilterCondition(Exception):
        """data_in["filter_blocks"][n]["operator"] value not in GryphonProtocolFilterCondition
        """

        def __init__(self, arg1=None):
            self.arg1 = arg1
            super(Gryphon.ValueNotInFilterCondition, self).__init__(arg1)

    class ValueNotInFT(Exception):
        """value not in GryphonProtocolFT
        """

        def __init__(self, arg1=None):
            self.arg1 = arg1
            super(Gryphon.ValueNotInFT, self).__init__(arg1)

    class PatternNotFound(Exception):
        """data_in["filter_blocks"][n]["operator"] does not contained necessary "pattern" item
        """

        def __init__(self, arg1=None):
            self.arg1 = arg1
            super(Gryphon.PatternNotFound, self).__init__(arg1)

    class MaskNotFound(Exception):
        """data_in["filter_blocks"][n]["operator"] does not contained necessary "mask" item
        """

        def __init__(self, arg1=None):
            self.arg1 = arg1
            super(Gryphon.MaskNotFound, self).__init__(arg1)

    class LengthsNotEqual(Exception):
        """pattern and mask list lengths must be same
        """

        def __init__(self, arg1=None, arg2=None):
            self.arg1 = arg1
            self.arg2 = arg2
            super(Gryphon.LengthsNotEqual, self).__init__(arg1, arg2)

    class BitMaskNotFound(Exception):
        """block does not contained necessary "bit_mask" item
        """

        def __init__(self, arg1=None):
            self.arg1 = arg1
            super(Gryphon.BitMaskNotFound, self).__init__(arg1)

    class ValueNotFound(Exception):
        """data_in["filter_blocks"][n]["operator"] does not contained necessary "value" item
        """

        def __init__(self, arg1=None):
            self.arg1 = arg1
            super(Gryphon.ValueNotFound, self).__init__(arg1)

    class DataTypeNotFound(Exception):
        """data_in["filter_blocks"][n] does not contained necessary "data_type" item
        """

        def __init__(self, arg1=None):
            self.arg1 = arg1
            super(Gryphon.DataTypeNotFound, self).__init__(arg1)

    class ValueNotInFilterDataType(Exception):
        """data_in["filter_blocks"][n]["data_type"] value not in GryphonProtocolFilterDataType
        """

        def __init__(self, arg1=None):
            self.arg1 = arg1
            super(Gryphon.ValueNotInFilterDataType, self).__init__(arg1)

    class ValueNotInModFilter(Exception):
        """action value not in GryphonProtocolModFilter
        """

        def __init__(self, arg1=None):
            self.arg1 = arg1
            super(Gryphon.ValueNotInModFilter, self).__init__(arg1)

    class ValueOutOfRange(Exception):
        """value out of range
        """

        def __init__(self, arg1=None):
            self.arg1 = arg1
            super(Gryphon.ValueOutOfRange, self).__init__(arg1)

    class ValueNotValid(Exception):
        """value not valid
        """

        def __init__(self, arg1=None):
            self.arg1 = arg1
            super(Gryphon.ValueNotValid, self).__init__(arg1)

    class HdrNotFound(Exception):
        """data_in does not contained necessary "hdr" item
        """

        def __init__(self, arg1=None):
            self.arg1 = arg1
            super(Gryphon.HdrNotFound, self).__init__(arg1)

    class HdrLenNotFound(Exception):
        """data_in does not contained necessary "hdrlen" item
        """

        def __init__(self, arg1=None):
            self.arg1 = arg1
            super(Gryphon.HdrLenNotFound, self).__init__(arg1)

    class SignalNameNotFound(Exception):
        """data_in does not contained necessary "signal_name" item
        """

        def __init__(self, arg1=None):
            self.arg1 = arg1
            super(Gryphon.SignalNameNotFound, self).__init__(arg1)

    class ExtraLenNotFound(Exception):
        """data_in does not contained necessary "hdrlen" item
        """

        def __init__(self, arg1=None):
            self.arg1 = arg1
            super(Gryphon.ExtraLenNotFound, self).__init__(arg1)

    class MessageListNotFound(Exception):
        """data_in does not contained necessary "message_list" item
        """

        def __init__(self, arg1=None):
            self.arg1 = arg1
            super(Gryphon.MessageListNotFound, self).__init__(arg1)

    class NotYetImplemented(Exception):
        """command not implemented
            Usage:
                raise Gryphon.NotYetImplemented
        """

        def __init__(self, arg1=None):
            self.arg1 = arg1
            super(Gryphon.NotYetImplemented, self).__init__(arg1)

    def CMD_EVENT_ENABLE(self, chan, value_in=0):
        """event enable

        Args:
            chan
            value_in, 0 is all events, n is event number

        Pre:
            CMD_SERVER_REG()
            1 <= chan <= n_channels

        Post:

        Returns:
            A dictionary containing "response_return_code" as one
            of the GryphonProtocolResp RESP_ codes.
            Also return "GCprotocol" containing entire GCprotocol message bytes.

        Raises:
            None.
        """
        # done 20190103
        if chan == 0:
            raise self.ChannelNotValid(chan)
        databa = bytearray()
        databa.extend([value_in])
        # TODO this is unusual, will not work with size=8
        return self._build_and_send_command(
            dst=self.SD_CARD,
            dstchan=chan,
            cmd=self.BCMD_EVENT_ENABLE,
            data=databa,
            unusual_length=5,
        )

    def CMD_EVENT_DISABLE(self, chan, value_in):
        """event enable

        Args:
            chan
            value_in, 0 is all events, n is event number

        Pre:
            CMD_SERVER_REG()
            1 <= chan <= n_channels

        Post:

        Returns:
            A dictionary containing "response_return_code" as one
            of the GryphonProtocolResp RESP_ codes.
            Also return "GCprotocol" containing entire GCprotocol message bytes.

        Raises:
            None.
        """
        # done 20190103
        # TODO we need to verify that get tx loop work for multiple clients and channels
        if chan == 0:
            raise self.ChannelNotValid(chan)
        databa = bytearray()
        databa.extend([value_in])
        # TODO this is unusual, will not work with size=8
        return self._build_and_send_command(
            dst=self.SD_CARD,
            dstchan=chan,
            cmd=self.BCMD_EVENT_DISABLE,
            data=databa,
            unusual_length=5,
        )

    def CMD_INIT(self, dstchan, dst=GryphonProtocolSD.SD_CARD, value_in=0):
        """init chan or sched

        Args:
            value_in is one of GryphonProtocolInit
            dst is either SD_CARD or SD_SCHED

        Pre:
            CMD_SERVER_REG()
            0 <= dstchan <= n_channels
            for backward compatibility, if dstchan is 0, init the scheduler

        Post:

        Returns:
            A dictionary containing "response_return_code" as one
            of the GryphonProtocolResp RESP_ codes.
            Also return "GCprotocol" containing entire GCprotocol message bytes.

        Raises:
            None.
        """
        # done 20190103
        if dstchan == 0:
            dst = GryphonProtocolSD.SD_SCHED

        if not isinstance(value_in, six.integer_types):
            return False

        values = dir(GryphonProtocolInit)
        # filter out all of the __x__ attributes
        values[:] = [x for x in values if "__" not in x]
        filtervalues = []
        # get the actual values of all of the commands, using the attribute names
        filtervalues.extend([getattr(GryphonProtocolInit, x) for x in values])
        if value_in not in filtervalues:
            # print "WARNING CMD_INIT() value={} not in {}".format(value_in, filtervalues)
            # return False
            # TODO ?
            pass

        databa = bytearray()
        databa.extend([value_in])

        # TODO this is unusual, will not work with size=8
        reply = self._build_and_send_command(
            dst=dst, dstchan=dstchan, cmd=self.BCMD_INIT, data=databa, unusual_length=5
        )

        return reply

    def CMD_CARD_SET_FILTER_MODE(self, chan, value_in):
        """set filter mode

        Args:
            channel
            value_in is one of GryphonProtocolSetFilterMode

        Pre:
            CMD_SERVER_REG()
            1 <= chan <= n_channels

        Post:

        Returns:
            True on success, otherwise False

        Raises:
            None.
        """

        # done 20190103
        # TODO we need to verify that get tx loop work for multiple clients and channels
        if chan == 0:
            raise self.ChannelNotValid(chan)
        if not isinstance(value_in, six.integer_types):
            raise self.ValueNotInt(value_in)

        values = dir(GryphonProtocolSetFilterMode)
        # filter out all of the __x__ attributes
        values[:] = [x for x in values if "__" not in x]
        filtervalues = []
        # get the actual values of all of the commands, using the attribute names
        filtervalues.extend([getattr(GryphonProtocolSetFilterMode, x) for x in values])
        if value_in not in filtervalues:
            # print "WARNING CMD_CARD_SET_FILTER_MODE() value={} not in {}".format(value_in, filtervalues)
            # TODO ?
            # return False
            pass

        databa = bytearray()
        databa.extend([value_in])
        return self._build_and_send_command(
            dst=self.SD_CARD,
            dstchan=chan,
            cmd=self.BCMD_CARD_SET_FILTER_MODE,
            data=databa,
        )

    def CMD_CARD_GET_FILTER_MODE(self, chan):
        """get filter mode

        Args:
            channel

        Pre:
            CMD_SERVER_REG()
            1 <= chan <= n_channels

        Post:

        Returns:
            data one of GryphonProtocolSetFilterMode

        Raises:
            None.
        """
        # done 20190103
        if chan == 0:
            raise self.ChannelNotValid(chan)

        reply_dict = self._build_and_send_command(
            dst=self.SD_CARD, dstchan=chan, cmd=self.BCMD_CARD_GET_FILTER_MODE
        )
        if sys.version_info[0] < 3:
            reply_dict.update(
                {"filter_mode": ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][8])}
            )
        else:
            reply_dict.update(
                {"filter_mode": reply_dict["GCprotocol"]["body"][self.RAWDATA][8]}
            )
        return reply_dict

    def _padding_number(self, msg_len):
        """gryphon protocol padding

        Args:
            message length

        Pre:
            None.

        Post:
            number of return bytes is 4 minus len mod 4

        Returns:
            an array containing either 0,1,2, or 3 padding bytes, either
            [] for mod4 = 0
            [0, 0, 0] for mod4 = 1
            [0, 0] for mod4 = 2
            [0] for mod4 = 3

        Raises:
            None.
        """
        padding = [[], [0, 0, 0], [0, 0], [0]]
        # print "-->>>>>>>>>>>>>>>>>-----len {} {} padding {}".format(msg_len, msg_len % 4, padding[msg_len % 4])
        return padding[msg_len % 4]

    def CMD_CARD_ADD_FILTER(self, chan, data_in):
        #
        # ----------------------------------------------------------------------
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        # ----------------------------------------------------------------------
        #
        """add filter
            see also CMD_CARD_GET_FILTER()

        Args:
            chan
            data in a dictionay
                data_in["flags"] - one or more of GryphonProtocolFilterFlags
                IF flag | FILTER_FLAG_SAMPLING_ACTIVE
                    data_in["time_interval"] -
                    data_in["message_count"] -
                data_in["filter_blocks"][0]["byte_offset"] -
                data_in["filter_blocks"][0]["data_type"] - one of GryphonProtocolFilterDataType
                data_in["filter_blocks"][0]["operator"] - one of GryphonProtocolFilterCondition
                IF operator is BIT_FIELD_CHECK
                    data_in["filter_blocks"][0]["pattern"][] - list of header or data bytes
                    data_in["filter_blocks"][0]["mask"][] - list of masks
                ELSE
                    data_in["filter_blocks"][0]["value"] - list of bytes

        Pre:
            CMD_SERVER_REG()
            1 <= chan <= n_channels

        Post:

        Returns:
            1-byte filter handle

        Raises:
            None.
        """
        # done 20190103
        # TODO for some unknown reason, the padding on last block of command CMD_CARD_ADD_FILTER needs to be 8-bytes
        # data_in.extend([0, 0, 0, 0])

        # 20190108 raise an exception instead of returning False
        # ----------------------------------------------------------------------
        # exceptions for this function
        # ----------------------------------------------------------------------
        if chan == 0:
            raise self.ChannelNotValid(chan)

        data = bytearray()
        if "flags" not in data_in:
            raise self.FlagsNotFound

        flags = data_in["flags"]
        data.extend([flags])

        if "filter_blocks" not in data_in:
            raise self.FilterBlocksNotFound

        data.extend([len(data_in["filter_blocks"])])
        if flags & GryphonProtocolFilterFlags.FILTER_FLAG_SAMPLING_ACTIVE:
            if "time_interval" not in data_in:
                raise self.TimeIntervalNotFound
            if "message_count" not in data_in:
                raise self.MsgCountNotFound
            time_interval1 = (data_in["time_interval"] & 0xFF00) >> 8
            time_interval2 = (data_in["time_interval"] & 0x00FF) >> 0
            message_count = data_in["message_count"]
            data.extend([time_interval1, time_interval2])  # time_interval
            data.extend([message_count])  # time_interval
        else:
            data.extend([0, 0])  # time_interval
            data.extend([0])  # message_count
        data.extend([0, 0, 0])  # resvd

        for block in data_in["filter_blocks"]:
            # block n
            if "byte_offset" not in block:
                raise self.ByteOffsetNotFound
            byte_offset1 = (block["byte_offset"] & 0xFF00) >> 8
            byte_offset2 = (block["byte_offset"] & 0x00FF) >> 0
            data.extend([byte_offset1, byte_offset2])  # byte offset

            if "operator" not in block:
                raise self.OperatorNotFound

            values = dir(GryphonProtocolFilterCondition)
            # filter out all of the __x__ attributes
            values[:] = [x for x in values if "__" not in x]
            filtervalues = []
            # get the actual values of all of the commands, using the attribute names
            filtervalues.extend(
                [getattr(GryphonProtocolFilterCondition, x) for x in values]
            )
            if block["operator"] not in filtervalues:
                raise self.ValueNotInFilterCondition(block["operator"])

            if block["operator"] == GryphonProtocolFilterCondition.BIT_FIELD_CHECK:
                if "pattern" not in block:
                    raise self.PatternNotFound
                if "mask" not in block:
                    raise self.MaskNotFound
                first_field_len1 = (len(block["pattern"]) & 0xFF00) >> 8
                first_field_len2 = (len(block["pattern"]) & 0x00FF) >> 0
            else:
                if "value" not in block:
                    raise self.ValueNotFound
                first_field_len1 = (len(block["value"]) & 0xFF00) >> 8
                first_field_len2 = (len(block["value"]) & 0x00FF) >> 0
            data.extend([first_field_len1, first_field_len2])  # len

            if "data_type" not in block:
                raise self.DataTypeNotFound
            values = dir(GryphonProtocolFilterDataType)
            # filter out all of the __x__ attributes
            values[:] = [x for x in values if "__" not in x]
            filtervalues = []
            # get the actual values of all of the commands, using the attribute names
            filtervalues.extend(
                [getattr(GryphonProtocolFilterDataType, x) for x in values]
            )
            if block["data_type"] not in filtervalues:
                raise self.ValueNotInFilterDataType(block["data_type"])
            dtype = block["data_type"]
            data.extend([dtype])  # data type
            oper = block["operator"]
            data.extend([oper])  # operator
            data.extend([0, 0])  # resvd 2 bytes
            if block["operator"] == GryphonProtocolFilterCondition.BIT_FIELD_CHECK:
                data.extend(block["pattern"])
                data.extend(block["mask"])
                bytecount = len(block["pattern"]) + len(block["mask"])
            else:
                data.extend(block["value"])
                bytecount = len(block["value"])

            # calculate padding, 0-3 bytes
            new_padding = self._padding_number(bytecount)
            data.extend(new_padding)  # padding

        # TODO for some unknown reason, the padding on last block of command CMD_CARD_ADD_FILTER needs to be 8-bytes
        # data.extend([0, 0, 0, 0])

        reply_dict = self._build_and_send_command(
            dst=self.SD_CARD, dstchan=chan, cmd=self.BCMD_CARD_ADD_FILTER, data=data
        )
        if sys.version_info[0] < 3:
            reply_dict.update(
                {
                    "filter_handle": ord(
                        reply_dict["GCprotocol"]["body"][self.RAWDATA][8]
                    )
                }
            )
        else:
            reply_dict.update(
                {"filter_handle": reply_dict["GCprotocol"]["body"][self.RAWDATA][8]}
            )
        return reply_dict

    def CMD_CARD_MODIFY_FILTER(self, chan, action, filter_handle=0):
        """modify filter mode

        Args:
            channel
            action - one of GryphonProtocolModFilter
            filter handle - 0 is all filters, 1 to 0xFE is filter handle

        Pre:
            CMD_SERVER_REG()
            CMD_CARD_ADD_FILTER()
            1 <= chan <= n_channels

        Post:

        Returns:
            1-byte filter handle

        Raises:
            None.
        """
        # done 20190103
        if chan == 0:
            raise self.ChannelNotValid(chan)

        data_value = bytearray()

        values = dir(GryphonProtocolModFilter)
        # filter out all of the __x__ attributes
        values[:] = [x for x in values if "__" not in x]
        filtervalues = []
        # get the actual values of all of the commands, using the attribute names
        filtervalues.extend([getattr(GryphonProtocolModFilter, x) for x in values])
        if action not in filtervalues:
            raise self.ValueNotInModFilter(action)
        if (filter_handle < 0) or (filter_handle > 0xFE):
            raise self.ValueOutOfRange(filter_handle)

        data_value.extend([filter_handle])
        data_value.extend([action])
        data_value.extend([0, 0])  # padding

        return self._build_and_send_command(
            dst=self.SD_CARD,
            dstchan=chan,
            cmd=self.BCMD_CARD_MODIFY_FILTER,
            data=data_value,
        )

    def CMD_CARD_SET_DEFAULT_FILTER(self, chan, value_in):
        """set default filter

        Args:
            channel
            value of action as integer as one of GryphonProtocolSetDefaultFilter

        Pre:
            CMD_SERVER_REG()
            1 <= chan <= n_channels

        Post:

        Returns:
            True on success

        Raises:
            None.
        """
        # done 20190103
        if chan == 0:
            raise self.ChannelNotValid(chan)

        if not isinstance(value_in, six.integer_types):
            raise self.ValueNotInt(chan)

        values = dir(GryphonProtocolSetDefaultFilter)
        # filter out all of the __x__ attributes
        values[:] = [x for x in values if "__" not in x]
        filtervalues = []
        # get the actual values of all of the commands, using the attribute names
        filtervalues.extend(
            [getattr(GryphonProtocolSetDefaultFilter, x) for x in values]
        )
        if value_in not in filtervalues:
            # print "WARNING CMD_CARD_SET_DEFAULT_FILTER() value={} not in {}".format(value_in, filtervalues)
            # TODO ?
            pass
        else:
            pass
            # print "DEBUG CMD_CARD_SET_DEFAULT_FILTER() value={} IS in {}".format(value_in, filtervalues)
            # return False

        data_value = bytearray()
        data_value.extend([value_in])
        return self._build_and_send_command(
            dst=self.SD_CARD,
            dstchan=chan,
            cmd=self.BCMD_CARD_SET_DEFAULT_FILTER,
            data=data_value,
        )

    def CMD_CARD_GET_DEFAULT_FILTER(self, chan):
        """set default filter

        Args:
            channel

        Pre:
            CMD_SERVER_REG()
            1 <= chan <= n_channels

        Post:

        Returns:
            value one of GryphonProtocolSetDefaultFilter

        Raises:
            None.
        """
        # done 20190103
        if chan == 0:
            raise self.ChannelNotValid(chan)

        reply_dict = self._build_and_send_command(
            dst=self.SD_CARD, dstchan=chan, cmd=self.BCMD_CARD_GET_DEFAULT_FILTER
        )
        if sys.version_info[0] < 3:
            reply_dict.update(
                {
                    "default_filter_mode": ord(
                        reply_dict["GCprotocol"]["body"][self.RAWDATA][8]
                    )
                }
            )
        else:
            reply_dict.update(
                {
                    "default_filter_mode": reply_dict["GCprotocol"]["body"][
                        self.RAWDATA
                    ][8]
                }
            )
        return reply_dict

    def CMD_CARD_GET_EVNAMES(self, chan):
        """get event names

        Args:
            channel

        Pre:
            CMD_SERVER_REG()
            1 <= chan <= n_channels

        Post:

        Returns:
            returns a list of dict

        Raises:
            None.
        """
        # done 20190103
        if chan == 0:
            raise self.ChannelNotValid(chan)

        reply_dict = self._build_and_send_command(
            dst=self.SD_CARD, dstchan=chan, cmd=self.BCMD_CARD_GET_EVNAMES
        )
        reply1 = []  # returns a list of dict
        for item in range(
            8, reply_dict["GCprotocol"]["framehdr"][self.LEN], 20
        ):  # increment by 20 bytes
            event = {}
            if sys.version_info[0] < 3:
                event["id"] = ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][item])
                event["name"] = "".join(
                    reply_dict["GCprotocol"]["body"][self.RAWDATA][item + 1 : item + 20]
                )
            else:
                event["id"] = reply_dict["GCprotocol"]["body"][self.RAWDATA][item]
                event["name"] = "".join(
                    map(
                        chr,
                        reply_dict["GCprotocol"]["body"][self.RAWDATA][
                            item + 1 : item + 20
                        ],
                    )
                )
            reply1.append(event)
        reply_dict.update({"event_names": reply1})
        return reply_dict

    def CMD_CARD_SET_SPEED(self, chan, value_in):
        """set speed

        Args:
            channel

        Pre:
            CMD_SERVER_REG()
            1 <= chan <= n_channels

        Post:

        Returns:
            None.

        Raises:
            None.
        """
        if chan == 0:
            raise self.ChannelNotValid(chan)

        data_value = bytearray()
        data_value.extend([value_in])
        return self._build_and_send_command(
            dst=self.SD_CARD,
            dstchan=chan,
            cmd=self.BCMD_CARD_SET_SPEED,
            data=data_value,
        )

    def CMD_CARD_GET_SPEED(self, chan):
        """get speed

        Args:
            channel

        Pre:
            CMD_SERVER_REG()
            1 <= chan <= n_channels

        Post:

        Returns:
            None.

        Raises:
            None.
        """
        if chan == 0:
            raise self.ChannelNotValid(chan)

        return self._build_and_send_command(
            dst=self.SD_CARD, dstchan=chan, cmd=self.BCMD_CARD_SET_SPEED, data=None
        )

    def CMD_CARD_GET_FILTER(self, chan, filter_handle):
        #
        # ----------------------------------------------------------------------
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        # ----------------------------------------------------------------------
        #
        """get filter
           see also CMD_CARD_ADD_FILTER()

        Args:
            channel
            filter handle

        Pre:
            CMD_SERVER_REG()
            1 <= chan <= n_channels

        Post:

        Returns:
            value one of GryphonProtocolSetDefaultFilter

        Raises:
            None.
        """
        # done 20190103
        data_value = bytearray()
        data_value.extend([filter_handle])
        reply_dict = self._build_and_send_command(
            dst=self.SD_CARD,
            dstchan=chan,
            cmd=self.BCMD_CARD_GET_FILTER,
            data=data_value,
        )
        index = 8
        reply_dict["GCprotocol"]["body"].update({"data": {}})
        if sys.version_info[0] < 3:
            reply_dict["GCprotocol"]["body"]["data"].update(
                {"flags": ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][index])}
            )
            index += 1
            nblocks = ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][index])
            index += 1
            index += 6
            filter_blocks = []
            for block_number in range(0, nblocks):
                filter_block = {}
                filter_block.update({"filter_block_number": block_number + 1})
                byte_offset = (
                    ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][index]) << 8
                )
                index += 1
                byte_offset += (
                    ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][index]) << 0
                )
                filter_block.update(
                    {
                        "byte_offset": ord(
                            reply_dict["GCprotocol"]["body"][self.RAWDATA][index]
                        )
                    }
                )
                index += 1

                field_len = (
                    ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][index]) << 8
                )
                index += 1
                field_len += (
                    ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][index]) << 0
                )
                index += 1

                filter_block.update(
                    {
                        "data_type": ord(
                            reply_dict["GCprotocol"]["body"][self.RAWDATA][index]
                        )
                    }
                )
                index += 1

                operator = ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][index])
                filter_block.update({"operator": operator})
                # print "------------------->>>>>>>>>>----------index {} operator {}".format(index, operator)
                index += 1
                index += 2  # reserved 0x0000
                if operator == GryphonProtocolFilterCondition.BIT_FIELD_CHECK:
                    pattern = []
                    bytenumber = 0
                    while bytenumber < field_len:
                        bytenumber += 1
                        # print "------------------->>>>>>>>>>----------index {} pattern {}".format(index, pattern)
                        pattern.append(
                            ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][index])
                        )
                        index += 1
                    filter_block.update({"pattern": pattern})
                    mask = []
                    bytenumber = 0
                    while bytenumber < field_len:
                        bytenumber += 1
                        mask.append(
                            ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][index])
                        )
                        index += 1
                    filter_block.update({"mask": mask})
                else:
                    value = []
                    bytenumber = 0
                    while bytenumber < field_len:
                        bytenumber += 1
                        # print "------------------->>>>>>>>>>----------index {} value {}".format(index, value)
                        value.append(
                            ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][index])
                        )
                        index += 1
                    filter_block.update({"value": value})

                filter_blocks.append(filter_block)
        else:
            reply_dict["GCprotocol"]["body"]["data"].update(
                {"flags": reply_dict["GCprotocol"]["body"][self.RAWDATA][index]}
            )
            index += 1
            nblocks = reply_dict["GCprotocol"]["body"][self.RAWDATA][index]
            index += 1
            index += 6
            filter_blocks = []
            for block_number in range(0, nblocks):
                filter_block = {}
                filter_block.update({"filter_block_number": block_number + 1})
                byte_offset = reply_dict["GCprotocol"]["body"][self.RAWDATA][index] << 8
                index += 1
                byte_offset += (
                    reply_dict["GCprotocol"]["body"][self.RAWDATA][index] << 0
                )
                filter_block.update(
                    {
                        "byte_offset": reply_dict["GCprotocol"]["body"][self.RAWDATA][
                            index
                        ]
                    }
                )
                index += 1

                field_len = reply_dict["GCprotocol"]["body"][self.RAWDATA][index] << 8
                index += 1
                field_len += reply_dict["GCprotocol"]["body"][self.RAWDATA][index] << 0
                index += 1

                filter_block.update(
                    {"data_type": reply_dict["GCprotocol"]["body"][self.RAWDATA][index]}
                )
                index += 1

                operator = reply_dict["GCprotocol"]["body"][self.RAWDATA][index]
                filter_block.update({"operator": operator})
                # print "------------------->>>>>>>>>>----------index {} operator {}".format(index, operator)
                index += 1
                index += 2  # reserved 0x0000
                if operator == GryphonProtocolFilterCondition.BIT_FIELD_CHECK:
                    pattern = []
                    bytenumber = 0
                    while bytenumber < field_len:
                        bytenumber += 1
                        # print "------------------->>>>>>>>>>----------index {} pattern {}".format(index, pattern)
                        pattern.append(
                            reply_dict["GCprotocol"]["body"][self.RAWDATA][index]
                        )
                        index += 1
                    filter_block.update({"pattern": pattern})
                    mask = []
                    bytenumber = 0
                    while bytenumber < field_len:
                        bytenumber += 1
                        mask.append(
                            reply_dict["GCprotocol"]["body"][self.RAWDATA][index]
                        )
                        index += 1
                    filter_block.update({"mask": mask})
                else:
                    value = []
                    bytenumber = 0
                    while bytenumber < field_len:
                        bytenumber += 1
                        # print "------------------->>>>>>>>>>----------index {} value {}".format(index, value)
                        value.append(
                            reply_dict["GCprotocol"]["body"][self.RAWDATA][index]
                        )
                        index += 1
                    filter_block.update({"value": value})

                filter_blocks.append(filter_block)
        reply_dict["GCprotocol"]["body"]["data"].update(
            {"filter_blocks": filter_blocks}
        )

        return reply_dict

    def CMD_CARD_GET_FILTER_HANDLES(self, chan):
        """get filter handles

        Args:
            channel

        Pre:
            CMD_SERVER_REG()
            1 <= chan <= n_channels

        Post:

        Returns:
            array of bytes

        Raises:
            None.
        """
        # done 20190103
        reply_dict = self._build_and_send_command(
            dst=self.SD_CARD, dstchan=chan, cmd=self.BCMD_CARD_GET_FILTER_HANDLES
        )
        filter_handles = []
        if sys.version_info[0] < 3:
            nfilters = ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][8])
            index = 9
            for _ in range(0, nfilters):
                filter_handles.append(
                    ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][index])
                )
                index += 1
        else:
            nfilters = reply_dict["GCprotocol"]["body"][self.RAWDATA][8]
            index = 9
            for _ in range(0, nfilters):
                filter_handles.append(
                    reply_dict["GCprotocol"]["body"][self.RAWDATA][index]
                )
                index += 1
        reply_dict["GCprotocol"]["body"].update({"data": {}})
        reply_dict["GCprotocol"]["body"]["data"].update(
            {"filter_handles": filter_handles}
        )
        return reply_dict

    def CMD_CARD_TX(self, msg):
        """tx

        Args:
            msg
                ['framehdr']['src'] - (optional)
                ['framehdr']['srcchan'] - (optional)
                ['framehdr']['dst'] - (optional)
                ['framehdr']['dstchan'] -
                ['framehdr']['frametype'] - (optional), default is FT_DATA
                ['body']['data']['hdrlen'] - (optional)
                ['body']['data']['hdrbits'] - (optional)
                ['body']['data']['datalen'] - (optional)
                ['body']['data']['extralen'] - (optional)
                ['body']['data']['mode'] - (optional)
                ['body']['data']['pri'] - (optional)
                ['body']['data']['status'] - (optional)
                ['body']['data']['timestamp'] - (optional)
                ['body']['data']['context'] - (optional)
                ['body']['data']['hdr'] - [] list of header bytes
                ['body']['data']['data'] - (optional) [] list of data bytes
                ['body']['data']['extra'] - (optional) [] list of extra bytes
                ['body']['text'] - (optional), for FT_TEXT message

        Pre:
            CMD_SERVER_REG()
            1 <= chan <= n_channels

        Post:
            tbd

        Returns:
            array of bytes

        Raises:
            None.
        """
        # 20190615
        gcframes = bytearray()

        # hdrlen
        # %%%WARNING: must compute hdrlen before doing hdr[]

        if "framehdr" not in msg:
            raise self.FrameHdrNotFound

        if "dstchan" not in msg["framehdr"]:
            raise self.FrameHdrNotFound
        dstchan = msg["framehdr"]["dstchan"]
        chan = dstchan

        # default FT_DATA
        if "frametype" in msg["framehdr"]:
            # TODO create defines to replace constants
            frametype = msg["framehdr"]["frametype"] & 0x3F
        else:
            frametype = msg["framehdr"][
                "frametype"
            ] = GryphonProtocolFT.FT_DATA  # default

        if "body" not in msg:
            raise self.BodyNotFound

        if frametype == GryphonProtocolFT.FT_DATA:

            if "data" not in msg["body"]:
                raise self.DataNotFound

            data_in = msg["body"]["data"]

            # hdrlen
            # %%%WARNING: must compute hdrlen before doing hdr[]
            hdrlen = None
            if "hdrlen" in data_in:
                if isinstance(data_in["hdrlen"], six.integer_types):
                    hdrlen = data_in["hdrlen"]
                else:
                    # TODO
                    raise self.ValueOutOfRange(data_in["hdrlen"])

            # hdr
            if "hdr" not in data_in:
                raise self.HdrNotFound()

            hdr = []
            if isinstance(data_in["hdr"], (list, bytearray)):
                if hdrlen is not None:
                    # only use hdrlen number of elems from hdr[]
                    maxhdr = min(hdrlen, len(data_in["hdr"]))
                    for ind in range(0, maxhdr):
                        hdr.append(data_in["hdr"][ind])
                else:
                    hdrlen = len(data_in["hdr"])
                    hdr = data_in["hdr"]
            elif isinstance(data_in["hdr"], int):
                if hdrlen is None:
                    raise self.HdrLenNotFound()
                # split hdr into hdrlen number of bytes
                for ind in range(0, hdrlen):
                    mask = 0x00FF << (8 * ind)
                    num = data_in["hdr"] * mask
                    mybyte = num >> (8 * ind)
                    hdr.append(mybyte)
                # reverse the list
                hdr.reverse()
            else:
                raise self.HdrNotFound(data_in["hdr"])

            # hdrbits
            hdrbits = 11  # CANbus 11-bit header, default
            if "hdrbits" in data_in:
                hdrbits = data_in["hdrbits"]
            else:
                if hdrlen == 1:  # LINbus header
                    hdrbits = 8
                elif hdrlen == 4:  # CANbus 29-bit header
                    hdrbits = 29
                else:
                    hdrbits = 11  # CANbus 11-bit header, default

            # datalen
            # %%%WARNING: must compute datalen before doing data[]
            datalen = None
            if "datalen" in data_in:
                if isinstance(data_in["datalen"], six.integer_types):
                    datalen = data_in["datalen"]
                else:
                    raise self.ValueOutOfRange(data_in["datalen"])
            else:
                if "data" in data_in:
                    datalen = len(data_in["data"])
                else:
                    datalen = 0  # default

            # convert into two bytes
            datalen1 = (datalen & 0xFF00) >> 8
            datalen2 = (datalen & 0x00FF) >> 0

            # data
            data = []
            if "data" in data_in:
                if isinstance(data_in["data"], (list, bytearray)):
                    maxdata = min(datalen, len(data_in["data"]))
                    for ind in range(0, maxdata):
                        data.append(data_in["data"][ind])
                else:
                    # is single int
                    data.append(data_in["data"])

            # extralen
            # %%%WARNING: must compute extralen before doing extra[]
            if "extralen" in data_in:
                if isinstance(data_in["extralen"], six.integer_types):
                    extralen = data_in["extralen"]
                else:
                    # TODO
                    raise self.ExtraLenNotFound()
            else:
                if "extra" in data_in:
                    extralen = len(data_in["extra"])
                else:
                    extralen = 0  # default

            # extra
            extra = None
            if "extra" in data_in:
                if isinstance(data_in["extra"], (list, bytearray)):
                    extra = []
                    maxextra = min(extralen, len(data_in["extra"]))
                    for ind in range(0, maxextra):
                        extra.append(data_in["extra"][ind])
                else:
                    # is single int
                    extra = []
                    extra.append(data_in["extra"])

            if "pri" in data_in:
                pri = data_in["pri"]
            else:
                pri = 0  # default

            if "status" in data_in:
                status = data_in["status"]
            else:
                status = 0  # default

            if "mode" in data_in:
                mode = data_in["mode"]
            else:
                mode = 0  # default

            if frametype == GryphonProtocolFT.FT_DATA:
                pass
            elif frametype == GryphonProtocolFT.FT_EVENT:
                # TODO implement FT_EVENT for CMD_MSGRESP_ADD()
                raise self.ValueNotValid(frametype)
            elif frametype == GryphonProtocolFT.FT_MISC:
                # TODO implement FT_MISC for CMD_MSGRESP_ADD()
                raise self.ValueNotValid(frametype)
            elif frametype == GryphonProtocolFT.FT_TEXT:
                # TODO implement FT_TEXT for CMD_MSGRESP_ADD()
                raise self.ValueNotValid(frametype)
            elif frametype == GryphonProtocolFT.FT_SIG:
                # TODO implement FT_SIG for CMD_MSGRESP_ADD()
                raise self.ValueNotValid(frametype)
            else:
                raise self.ValueNotInFT(frametype)

            # NOTE: we will need to go back and calculate the message len when all done
            gcframes.extend(
                [hdrlen, hdrbits, datalen1, datalen2]
            )  # BEACON data header, hdrlen, hdrbits, data len
            gcframes.extend(
                [extralen, mode, pri, status]
            )  # BEACON data header, extralen, mode, pri, status

            timestamp = []
            if "timestamp" in data_in:
                if isinstance(data_in["timestamp"], list):
                    timestamp = data_in["timestamp"]
                else:
                    # turn int into a list
                    # TODO
                    timestamp.append(((data_in["timestamp"] & 0xFF000000) >> 24) & 0xFF)
                    timestamp.append(((data_in["timestamp"] & 0x00FF0000) >> 16) & 0xFF)
                    timestamp.append(((data_in["timestamp"] & 0x0000FF00) >> 8) & 0xFF)
                    timestamp.append(((data_in["timestamp"] & 0x000000FF) >> 0) & 0xFF)
            else:
                timestamp = [0, 0, 0, 0]  # default

            gcframes.extend(timestamp)  # timestamp

            if "context" in data_in:
                context = data_in["context"]
            else:
                context = self.cmd_context  # default

            gcframes.extend([context, 0, 0, 0])  # context, reserved
            gcframes.extend(hdr)  # msg header
            if data is not None:
                gcframes.extend(data)  # msg data
            if extra is not None:
                gcframes.extend(extra)  # msg extra
            # padding
            lena = len(hdr) + len(data)
            gcframes.extend(self._padding(lena))  # padding

        elif frametype == GryphonProtocolFT.FT_TEXT:

            if "text" not in msg["body"]:
                raise self.TextNotFound

            lena = len(msg["body"]["text"])
            gcframes.extend(msg["body"]["text"])
            gcframes.extend(self._padding(lena))  # padding
        else:
            raise self.ValueNotInFT(msg["framehdr"]["frametype"])

        reply_dict = self._build_and_send_command(
            dst=self.SD_CARD, dstchan=chan, cmd=self.BCMD_CARD_TX, data=gcframes
        )
        return reply_dict

    def CMD_CARD_TX_LOOP_ON(self, chan):
        """tx loop on

        Args:
            channel

        Pre:
            CMD_SERVER_REG()
            1 <= chan <= n_channels

        Post:
            this is special. Since gryphon has no way to query loopback,
            we will implement get here in this class

        Returns:
            array of bytes

        Raises:
            None.
        """
        # done 20190103
        # TODO we need to verify that get tx loop work for multiple clients and channels
        if chan == 0:
            raise self.ChannelNotValid(chan)
        return self._build_and_send_command(
            dst=self.SD_CARD, dstchan=chan, cmd=self.BCMD_CARD_TX_LOOP_ON
        )

    def CMD_CARD_TX_LOOP_OFF(self, chan):
        """tx loop off

        Args:
            channel

        Pre:
            CMD_SERVER_REG()
            1 <= chan <= n_channels

        Post:
            this is special. Since gryphon has no way to query loopback,
            we will implement get here in this class

        Returns:
            array of bytes

        Raises:
            None.
        """
        # done 20190103
        # TODO we need to verify that get tx loop work for multiple clients and channels
        if chan == 0:
            raise self.ChannelNotValid(chan)
        return self._build_and_send_command(
            dst=self.SD_CARD, dstchan=chan, cmd=self.BCMD_CARD_TX_LOOP_OFF
        )

    def CMD_CARD_IOCTL(
        self,
        chan,
        ioctl_in,
        data_in=None,
        src=None,
        srcchan=None,
        dst=GryphonProtocolSD.SD_CARD,
        dstchan=None,
    ):
        #
        # ----------------------------------------------------------------------
        # pylint: disable=too-many-arguments
        # ----------------------------------------------------------------------
        #
        """ioctl

        Args:
            channel
            ioctl, one of GryphonProtocolIOCTL
            data_in, bytearray of the ioctl data bytes
            optional src
            optional srcchan
            optional dst
            optional dstchan

        Pre:
            CMD_SERVER_REG()
            1 <= chan <= n_channels
            ioctl in GryphonProtocolIOCTL

        Post:

        Returns:
            array of bytes

        Raises:
            None.
        """
        # done 20190103
        # set the dstchan to the channel, unless it is set by user
        # also, dst is SD_CARD, unless it is set by user
        if chan == 0:
            raise self.ChannelNotValid(chan)

        if dstchan is None:
            dstchan = chan

        databa = bytearray()
        ioctlbytes = struct.unpack("4B", struct.pack(">I", ioctl_in))
        databa.extend(ioctlbytes)
        if data_in is not None:
            # data_in not None
            databa.extend(data_in)
            new_padding = self._padding_number(len(databa))
            # print "--------------------------len(databa)={} new_padding {}".format(len(databa), new_padding)
            if src is None:
                if srcchan is None:
                    # src None, srcchan None
                    # let it go to defaults
                    reply_dict = self._build_and_send_command(
                        dst=dst,
                        dstchan=dstchan,
                        cmd=self.BCMD_CARD_IOCTL,
                        data=databa,
                        unusual_length=4 + len(databa) + len(new_padding),
                    )
                    # six.print_("====this one line {} {}".format(4109,reply_dict))
                else:
                    # src None, srcchan not None
                    reply_dict = self._build_and_send_command(
                        dst=dst,
                        dstchan=dstchan,
                        cmd=self.BCMD_CARD_IOCTL,
                        data=databa,
                        unusual_length=4 + len(databa) + len(new_padding),
                        srcchan=srcchan,
                    )
            else:
                if srcchan is None:
                    # src not None, srcchan None
                    reply_dict = self._build_and_send_command(
                        dst=dst,
                        dstchan=dstchan,
                        cmd=self.BCMD_CARD_IOCTL,
                        data=databa,
                        unusual_length=4 + len(databa) + len(new_padding),
                        src=src,
                    )
                else:
                    # src not None, srcchan not None
                    reply_dict = self._build_and_send_command(
                        dst=dst,
                        dstchan=dstchan,
                        cmd=self.BCMD_CARD_IOCTL,
                        data=databa,
                        unusual_length=4 + len(databa) + len(new_padding),
                        src=src,
                        srcchan=srcchan,
                    )

            reply_dict["GCprotocol"]["body"].update({"data": {}})
            reply_dict["GCprotocol"]["body"]["data"].update({})

            index = 0
            ioctl_data = []
            while index < len(data_in):
                # six.print_("====loop while index {} len data_in {}".format(index, len(data_in)))
                if sys.version_info[0] < 3:
                    ioctl_data.append(
                        ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][index + 8])
                    )
                else:
                    ioctl_data.append(
                        reply_dict["GCprotocol"]["body"][self.RAWDATA][index + 8]
                    )
                index += 1
            reply_dict["GCprotocol"]["body"]["data"].update({"ioctl_data": ioctl_data})

        else:
            # data_in None
            reply_dict = self._build_and_send_command(
                dst=dst, dstchan=chan, cmd=self.BCMD_CARD_IOCTL, data=databa
            )

        return reply_dict

    def CMD_SCHED_TX(self, chan, data_in, iterations=1):
        """sched tx

        Args:
            iterations of this sched
            channel

        Pre:
            CMD_SERVER_REG()
            1 <= chan <= n_channels, chan=None means to use the channel in the data_in

        Post:

        Returns:
            array of bytes

        Raises:
            None.
        """
        #
        # ----------------------------------------------------------------------
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        # ----------------------------------------------------------------------
        #
        # done 20190103
        if chan is not None:
            if chan == 0:
                raise self.ChannelNotValid(chan)

        databa = bytearray()
        interationbytes = struct.unpack("4B", struct.pack(">I", iterations))
        databa.extend(interationbytes)

        if "flags" in data_in:
            flags = struct.unpack("4B", struct.pack(">I", data_in["flags"]))
            databa.extend(flags)  # flags critical
        else:
            databa.extend([0, 0, 0, 0])  # flags critical

        if "message_list" not in data_in:
            raise self.MessageListNotFound()

        if not isinstance(data_in["message_list"], list):
            raise self.MessageListNotFound()

        for msg in data_in["message_list"]:
            if "sleep" in msg:
                sleep = struct.unpack("4B", struct.pack(">I", msg["sleep"]))
                databa.extend(sleep)  # sleep
            else:
                databa.extend([0, 0, 0, 0])  # sleep
            if "tx_count" in msg:
                txcount = struct.unpack("4B", struct.pack(">I", msg["tx_count"]))
                databa.extend(txcount)  # tx count # of times to tx this msg
            else:
                databa.extend(
                    [0, 0, 0, 1]
                )  # tx count # of times to tx this msg, default is 1
            if "tx_period" in msg:
                txper = struct.unpack("4B", struct.pack(">I", msg["tx_period"]))
                databa.extend(txper)  # tx period
            else:
                databa.extend([0, 0, 0, 0])  # tx period, default 100-milliseconds
            flags = 0
            if "skip_last" in msg:
                if msg["skip_last"] is True:
                    flags |= 0x01
            if "skip_first" in msg:
                if msg["skip_first"] is True:
                    flags |= 0x02
            if "period_in_microsec" in msg:
                if msg["period_in_microsec"] is True:
                    flags |= 0x04
            if chan is None:
                if "chan" in msg:
                    thischan = msg["chan"]
                else:
                    raise self.ChannelNotValid(chan)
            else:
                thischan = 0  # default is to use the dstchan as the channel

            databa.extend([0, flags, thischan, 0])  # flags, channel, resv

            # hdrlen
            # %%%WARNING: must compute hdrlen before doing hdr[]
            hdrlen = None
            if "hdrlen" in msg:
                if isinstance(msg["hdrlen"], six.integer_types):
                    hdrlen = msg["hdrlen"]
                else:
                    # TODO
                    raise self.ValueOutOfRange(msg["hdrlen"])

            # hdr
            if "hdr" not in msg:
                raise self.HdrNotFound()
            hdr = []
            if isinstance(msg["hdr"], (list, bytearray)):
                if hdrlen is not None:
                    # only use hdrlen number of elems from hdr[]
                    maxhdr = min(hdrlen, len(msg["hdr"]))
                    for ind in range(0, maxhdr):
                        hdr.append(msg["hdr"][ind])
                else:
                    hdrlen = len(msg["hdr"])
                    hdr = msg["hdr"]
            elif isinstance(msg["hdr"], int):
                if hdrlen is None:
                    raise self.HdrLenNotFound()
                # split hdr into hdrlen number of bytes
                for ind in range(0, hdrlen):
                    mask = 0x00FF << (8 * ind)
                    num = msg["hdr"] * mask
                    mybyte = num >> (8 * ind)
                    hdr.append(mybyte)
                # reverse the list
                hdr.reverse()
            else:
                raise self.HdrNotFound(msg["hdr"])

            # hdrbits
            hdrbits = 11  # CANbus 11-bit header, default
            if "hdrbits" in msg:
                hdrbits = msg["hdrbits"]
            else:
                if hdrlen == 1:  # LINbus header
                    hdrbits = 8
                elif hdrlen == 4:  # CANbus 29-bit header
                    hdrbits = 29
                else:
                    hdrbits = 11  # CANbus 11-bit header, default

            # datalen
            # %%%WARNING: must compute datalen before doing data[]
            datalen = None
            if "datalen" in msg:
                if isinstance(msg["datalen"], six.integer_types):
                    datalen = msg["datalen"]
                else:
                    raise self.ValueOutOfRange(msg["datalen"])
            else:
                if "data" in msg:
                    datalen = len(msg["data"])
                else:
                    datalen = 0  # default

            # convert into two bytes
            datalen1 = (datalen & 0xFF00) >> 8
            datalen2 = (datalen & 0x00FF) >> 0

            # data
            data = None
            if "data" in msg:
                if isinstance(msg["data"], (list, bytearray)):
                    data = []
                    maxdata = min(datalen, len(msg["data"]))
                    for ind in range(0, maxdata):
                        data.append(msg["data"][ind])
                else:
                    # is single int
                    data = []
                    data.append(msg["data"])

            # extralen
            # %%%WARNING: must compute extralen before doing extra[]
            if "extralen" in msg:
                if isinstance(msg["extralen"], six.integer_types):
                    extralen = msg["extralen"]
                else:
                    # TODO
                    raise self.ExtraLenNotFound()
            else:
                if "extra" in msg:
                    extralen = len(msg["extra"])
                else:
                    extralen = 0  # default

            # extra
            extra = None
            if "extra" in msg:
                if isinstance(msg["extra"], (list, bytearray)):
                    extra = []
                    maxextra = min(extralen, len(msg["extra"]))
                    for ind in range(0, maxextra):
                        extra.append(msg["extra"][ind])
                else:
                    # is single int
                    extra = []
                    extra.append(msg["extra"])

            if "pri" in msg:
                pri = msg["pri"]
            else:
                pri = 0  # default

            if "status" in msg:
                status = msg["status"]
            else:
                status = 0  # default

            timestamp = []
            if "timestamp" in msg:
                if isinstance(msg["timestamp"], list):
                    timestamp = msg["timestamp"]
                else:
                    # turn int into a list
                    # TODO
                    timestamp.append(((msg["timestamp"] & 0xFF000000) >> 24) & 0xFF)
                    timestamp.append(((msg["timestamp"] & 0x00FF0000) >> 16) & 0xFF)
                    timestamp.append(((msg["timestamp"] & 0x0000FF00) >> 8) & 0xFF)
                    timestamp.append(((msg["timestamp"] & 0x000000FF) >> 0) & 0xFF)
            else:
                timestamp = [0, 0, 0, 0]  # default

            if "mode" in msg:
                mode = msg["mode"]
            else:
                mode = 0  # default

            if "context" in msg:
                context = msg["context"]
            else:
                context = self.cmd_context  # default

            gcframe = bytearray()
            gcframe.extend(
                [hdrlen, hdrbits, datalen1, datalen2]
            )  # BEACON data header, hdrlen, hdrbits, data len
            gcframe.extend(
                [extralen, mode, pri, status]
            )  # BEACON data header, extralen, mode, pri, status
            gcframe.extend(timestamp)  # BEACON data header, timestamp
            gcframe.extend([context, 0, 0, 0])  # BEACON data header, context, resv
            gcframe.extend(hdr)  # msg header
            if data is not None:
                gcframe.extend(data)  # msg data
            if extra is not None:
                gcframe.extend(extra)  # msg extra
            databa.extend(gcframe)

            # do padding!
            databa.extend(self._padding(hdrlen + datalen + extralen))

        # print "-----------len-----"
        # print len(databa)

        reply_dict = self._build_and_send_command(
            dst=self.SD_SCHED, dstchan=chan, cmd=self.BCMD_SCHED_TX, data=databa
        )
        if reply_dict["response_return_code"] != GryphonProtocolResp.RESP_OK:
            return reply_dict
        if sys.version_info[0] < 3:
            sched_id = (
                (ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][8]) * 1024)
                + (ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][9]) * 512)
                + (ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][10]) * 256)
                + ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][11])
            )
        else:
            sched_id = (
                (reply_dict["GCprotocol"]["body"][self.RAWDATA][8] * 1024)
                + (reply_dict["GCprotocol"]["body"][self.RAWDATA][9] * 512)
                + (reply_dict["GCprotocol"]["body"][self.RAWDATA][10] * 256)
                + reply_dict["GCprotocol"]["body"][self.RAWDATA][11]
            )
        reply_dict.update({"schedule_id": sched_id})
        return reply_dict

    def CMD_SCHED_KILL_TX(self, chan, schedule_id):
        """sched tx

        Args:
            iterations of this sched
            channel
            schedule_id

        Pre:
            CMD_SERVER_REG()
            CMD_SCHED_MSG()
            1 <= chan <= n_channels

        Post:

        Returns:
            array of bytes

        Raises:
            None.
        """
        # done 20190103
        if chan == 0:
            raise self.ChannelNotValid(chan)

        databa = bytearray()
        interationbytes = struct.unpack("4B", struct.pack(">I", schedule_id))
        databa.extend(interationbytes)
        reply_dict = self._build_and_send_command(
            dst=self.SD_SCHED, dstchan=chan, cmd=self.BCMD_SCHED_KILL_TX, data=databa
        )
        return reply_dict

    def CMD_SCHED_MSG_REPLACE(self, schedule_id, data_in, index=1, flush=True, value=0):
        """sched tx

        Args:
            schedule_id - ID of the schedule
            index - index of the message in the schedule, default is 1
            flush - flush the delay queue, default is true
            value - time in milliseconds that Scheduler will output previously scheduled messages
            data_in - message header and data

        Pre:
            CMD_SERVER_REG()
            CMD_SCHED_MSG()

        Post:

        Returns:
            array of bytes

        Raises:
            None.
        """
        #
        # ----------------------------------------------------------------------
        # pylint: disable=too-many-arguments
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        # ----------------------------------------------------------------------
        # done 20190103
        databa = bytearray()

        # hdrlen
        # %%%WARNING: must compute hdrlen before doing hdr[]
        hdrlen = None
        if "hdrlen" in data_in:
            if isinstance(data_in["hdrlen"], six.integer_types):
                hdrlen = data_in["hdrlen"]
            else:
                # TODO
                raise self.ValueOutOfRange(data_in["hdrlen"])

        # hdr
        if "hdr" not in data_in:
            raise self.HdrNotFound()

        hdr = []
        if isinstance(data_in["hdr"], (list, bytearray)):
            if hdrlen is not None:
                # only use hdrlen number of elems from hdr[]
                maxhdr = min(hdrlen, len(data_in["hdr"]))
                for ind in range(0, maxhdr):
                    hdr.append(data_in["hdr"][ind])
            else:
                hdrlen = len(data_in["hdr"])
                hdr = data_in["hdr"]
        elif isinstance(data_in["hdr"], int):
            if hdrlen is None:
                raise self.HdrLenNotFound()
            # split hdr into hdrlen number of bytes
            for ind in range(0, hdrlen):
                mask = 0x00FF << (8 * ind)
                num = data_in["hdr"] * mask
                mybyte = num >> (8 * ind)
                hdr.append(mybyte)
            # reverse the list
            hdr.reverse()
        else:
            raise self.HdrNotFound(data_in["hdr"])

        # hdrbits
        hdrbits = 11  # CANbus 11-bit header, default
        if "hdrbits" in data_in:
            hdrbits = data_in["hdrbits"]
        else:
            if hdrlen == 1:  # LINbus header
                hdrbits = 8
            elif hdrlen == 4:  # CANbus 29-bit header
                hdrbits = 29
            else:
                hdrbits = 11  # CANbus 11-bit header, default

        # datalen
        # %%%WARNING: must compute datalen before doing data[]
        datalen = None
        if "datalen" in data_in:
            if isinstance(data_in["datalen"], six.integer_types):
                datalen = data_in["datalen"]
            else:
                raise self.ValueOutOfRange(data_in["datalen"])
        else:
            if "data" in data_in:
                datalen = len(data_in["data"])
            else:
                datalen = 0  # default

        # convert into two bytes
        datalen1 = (datalen & 0xFF00) >> 8
        datalen2 = (datalen & 0x00FF) >> 0

        # data
        data = None
        if "data" in data_in:
            if isinstance(data_in["data"], (list, bytearray)):
                data = []
                maxdata = min(datalen, len(data_in["data"]))
                for ind in range(0, maxdata):
                    data.append(data_in["data"][ind])
            else:
                # is single int
                data = []
                data.append(data_in["data"])

        # extralen
        # %%%WARNING: must compute extralen before doing extra[]
        if "extralen" in data_in:
            if isinstance(data_in["extralen"], six.integer_types):
                extralen = data_in["extralen"]
            else:
                # TODO
                raise self.ExtraLenNotFound()
        else:
            if "extra" in data_in:
                extralen = len(data_in["extra"])
            else:
                extralen = 0  # default

        # extra
        extra = None
        if "extra" in data_in:
            if isinstance(data_in["extra"], (list, bytearray)):
                extra = []
                maxextra = min(extralen, len(data_in["extra"]))
                for ind in range(0, maxextra):
                    extra.append(data_in["extra"][ind])
            else:
                # is single int
                extra = []
                extra.append(data_in["extra"])

        if "pri" in data_in:
            pri = data_in["pri"]
        else:
            pri = 0  # default

        if "status" in data_in:
            status = data_in["status"]
        else:
            status = 0  # default

        timestamp = []
        if "timestamp" in data_in:
            if isinstance(data_in["timestamp"], list):
                timestamp = data_in["timestamp"]
            else:
                # turn int into a list
                # TODO
                timestamp.append(((data_in["timestamp"] & 0xFF000000) >> 24) & 0xFF)
                timestamp.append(((data_in["timestamp"] & 0x00FF0000) >> 16) & 0xFF)
                timestamp.append(((data_in["timestamp"] & 0x0000FF00) >> 8) & 0xFF)
                timestamp.append(((data_in["timestamp"] & 0x000000FF) >> 0) & 0xFF)
        else:
            timestamp = [0, 0, 0, 0]  # default

        if "mode" in data_in:
            mode = data_in["mode"]
        else:
            mode = 0  # default

        if "context" in data_in:
            context = data_in["context"]
        else:
            context = self.cmd_context  # default

        sched_id = struct.unpack("4B", struct.pack(">I", schedule_id))
        databa.extend(sched_id)
        databa.extend([index])  # index
        if flush:
            databa.extend([1])  # flags, flush
        else:
            databa.extend([0])  # flags, flush
        value1 = (value & 0xFF00) >> 8
        value2 = (value & 0x00FF) >> 0
        databa.extend([value1, value2])  # value

        gcframe = bytearray()

        gcframe.extend(
            [hdrlen, hdrbits, datalen1, datalen2]
        )  # BEACON data header, hdrlen, hdrbits, data len
        gcframe.extend(
            [extralen, mode, pri, status]
        )  # BEACON data header, extralen, mode, pri, status
        gcframe.extend(timestamp)  # BEACON data header, timestamp
        gcframe.extend([context, 0, 0, 0])  # BEACON data header, context, resv
        gcframe.extend(hdr)  # msg header
        if data is not None:
            gcframe.extend(data)  # msg data
        if extra is not None:
            gcframe.extend(extra)  # msg extra
        databa.extend(gcframe)
        reply_dict = self._build_and_send_command(
            dst=self.SD_SCHED, dstchan=0, cmd=self.BCMD_SCHED_MSG_REPLACE, data=databa
        )
        return reply_dict

    def CMD_SCHED_GET_IDS(self):
        """sched tx

        Args:
            none

        Pre:
            CMD_SERVER_REG()

        Post:

        Returns:
            array of bytes

        Raises:
            None.
        """
        # done 20190103
        reply_dict = self._build_and_send_command(
            dst=self.SD_SCHED, dstchan=0, cmd=self.BCMD_SCHED_GET_IDS, data=None
        )
        if sys.version_info[0] < 3:
            nschedules = ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][8])
            reply_dict["GCprotocol"]["body"].update({"data": {}})
            reply_dict["GCprotocol"]["body"]["data"].update({"schedules": []})
            idx = 12
            for _ in range(0, nschedules):
                sched = {}
                sched["id"] = (
                    (ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][idx]) * 1024)
                    + (
                        ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][idx + 1])
                        * 512
                    )
                    + (
                        ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][idx + 2])
                        * 256
                    )
                    + ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][idx + 3])
                )
                idx += 4
                sched["src"] = ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][idx])
                idx += 1
                sched["srcchan"] = ord(
                    reply_dict["GCprotocol"]["body"][self.RAWDATA][idx]
                )
                idx += 1
                sched["dstchan"] = ord(
                    reply_dict["GCprotocol"]["body"][self.RAWDATA][idx]
                )
                idx += 1
                sched["context"] = ord(
                    reply_dict["GCprotocol"]["body"][self.RAWDATA][idx]
                )
                idx += 1
                sched["nmsg"] = (
                    (ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][idx]) * 1024)
                    + (
                        ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][idx + 1])
                        * 512
                    )
                    + (
                        ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][idx + 2])
                        * 256
                    )
                    + ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][idx + 3])
                )
                idx += 4

                sched["messages"] = []
                for _ in range(0, sched["nmsg"]):
                    msgs = {}
                    msgs["index"] = (
                        ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][idx]) * 256
                    ) + ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][idx + 1])
                    idx += 2
                    idx += 2
                    msgs["sleep"] = (
                        (
                            ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][idx])
                            * 1024
                        )
                        + (
                            ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][idx + 1])
                            * 512
                        )
                        + (
                            ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][idx + 2])
                            * 256
                        )
                        + ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][idx + 3])
                    )
                    idx += 4
                    msgs["count"] = (
                        (
                            ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][idx])
                            * 1024
                        )
                        + (
                            ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][idx + 1])
                            * 512
                        )
                        + (
                            ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][idx + 2])
                            * 256
                        )
                        + ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][idx + 3])
                    )
                    idx += 4
                    msgs["period"] = (
                        (
                            ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][idx])
                            * 1024
                        )
                        + (
                            ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][idx + 1])
                            * 512
                        )
                        + (
                            ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][idx + 2])
                            * 256
                        )
                        + ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][idx + 3])
                    )
                    idx += 4
                    msgs["flags"] = (
                        (
                            ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][idx])
                            * 1024
                        )
                        + (
                            ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][idx + 1])
                            * 512
                        )
                        + (
                            ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][idx + 2])
                            * 256
                        )
                        + ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][idx + 3])
                    )
                    idx += 2
                    msgs["channel"] = ord(
                        reply_dict["GCprotocol"]["body"][self.RAWDATA][idx]
                    )
                    idx += 1
                    idx += 1
                    sched["messages"].append(msgs)

                reply_dict["GCprotocol"]["body"]["data"]["schedules"].append(sched)
        else:
            nschedules = reply_dict["GCprotocol"]["body"][self.RAWDATA][8]
            reply_dict["GCprotocol"]["body"].update({"data": {}})
            reply_dict["GCprotocol"]["body"]["data"].update({"schedules": []})
            idx = 12
            for _ in range(0, nschedules):
                sched = {}
                sched["id"] = (
                    (reply_dict["GCprotocol"]["body"][self.RAWDATA][idx] * 1024)
                    + (reply_dict["GCprotocol"]["body"][self.RAWDATA][idx + 1] * 512)
                    + (reply_dict["GCprotocol"]["body"][self.RAWDATA][idx + 2] * 256)
                    + reply_dict["GCprotocol"]["body"][self.RAWDATA][idx + 3]
                )
                idx += 4
                sched["src"] = reply_dict["GCprotocol"]["body"][self.RAWDATA][idx]
                idx += 1
                sched["srcchan"] = reply_dict["GCprotocol"]["body"][self.RAWDATA][idx]
                idx += 1
                sched["dstchan"] = reply_dict["GCprotocol"]["body"][self.RAWDATA][idx]
                idx += 1
                sched["context"] = reply_dict["GCprotocol"]["body"][self.RAWDATA][idx]
                idx += 1
                sched["nmsg"] = (
                    (reply_dict["GCprotocol"]["body"][self.RAWDATA][idx] * 1024)
                    + (reply_dict["GCprotocol"]["body"][self.RAWDATA][idx + 1] * 512)
                    + (reply_dict["GCprotocol"]["body"][self.RAWDATA][idx + 2] * 256)
                    + reply_dict["GCprotocol"]["body"][self.RAWDATA][idx + 3]
                )
                idx += 4

                sched["messages"] = []
                for _ in range(0, sched["nmsg"]):
                    msgs = {}
                    msgs["index"] = (
                        reply_dict["GCprotocol"]["body"][self.RAWDATA][idx] * 256
                    ) + reply_dict["GCprotocol"]["body"][self.RAWDATA][idx + 1]
                    idx += 2
                    idx += 2
                    msgs["sleep"] = (
                        (reply_dict["GCprotocol"]["body"][self.RAWDATA][idx] * 1024)
                        + (
                            reply_dict["GCprotocol"]["body"][self.RAWDATA][idx + 1]
                            * 512
                        )
                        + (
                            reply_dict["GCprotocol"]["body"][self.RAWDATA][idx + 2]
                            * 256
                        )
                        + reply_dict["GCprotocol"]["body"][self.RAWDATA][idx + 3]
                    )
                    idx += 4
                    msgs["count"] = (
                        (reply_dict["GCprotocol"]["body"][self.RAWDATA][idx] * 1024)
                        + (
                            reply_dict["GCprotocol"]["body"][self.RAWDATA][idx + 1]
                            * 512
                        )
                        + (
                            reply_dict["GCprotocol"]["body"][self.RAWDATA][idx + 2]
                            * 256
                        )
                        + reply_dict["GCprotocol"]["body"][self.RAWDATA][idx + 3]
                    )
                    idx += 4
                    msgs["period"] = (
                        (reply_dict["GCprotocol"]["body"][self.RAWDATA][idx] * 1024)
                        + (
                            reply_dict["GCprotocol"]["body"][self.RAWDATA][idx + 1]
                            * 512
                        )
                        + (
                            reply_dict["GCprotocol"]["body"][self.RAWDATA][idx + 2]
                            * 256
                        )
                        + reply_dict["GCprotocol"]["body"][self.RAWDATA][idx + 3]
                    )
                    idx += 4
                    msgs["flags"] = (
                        (reply_dict["GCprotocol"]["body"][self.RAWDATA][idx] * 1024)
                        + (
                            reply_dict["GCprotocol"]["body"][self.RAWDATA][idx + 1]
                            * 512
                        )
                        + (
                            reply_dict["GCprotocol"]["body"][self.RAWDATA][idx + 2]
                            * 256
                        )
                        + reply_dict["GCprotocol"]["body"][self.RAWDATA][idx + 3]
                    )
                    idx += 2
                    msgs["channel"] = reply_dict["GCprotocol"]["body"][self.RAWDATA][
                        idx
                    ]
                    idx += 1
                    idx += 1
                    sched["messages"].append(msgs)

                reply_dict["GCprotocol"]["body"]["data"]["schedules"].append(sched)

        return reply_dict

    def FT_TEXT_TX(
        self,
        chan=GryphonProtocolSD.CH_BROADCAST,
        text_in="",
        read_loopback=False,
        timeout=0.25,
    ):
        """FT_TEXT tx
            The default is to broadcast a blank text string

        Args:
            chan, 1 <= chan <= n_channels, or CH_BROADCAST
            the text
            read_loopback - read the loopback-ed broadcast message and return it

        Pre:
            CMD_SERVER_REG()

        Post:

        Returns:

        Raises:
            None.
        """
        # done 20190103
        if chan == 0:
            raise self.ChannelNotValid(chan)
        databa = bytearray()
        if sys.version_info[0] < 3:
            databa.extend(text_in + "\0")
        else:
            databa.extend(bytes(text_in + "\0", encoding="ascii"))
        self._build_and_send_text(dst=self.src_type, dstchan=chan, text=databa)
        reply_dict = {"response_return_code": GryphonProtocolResp.RESP_OK}

        if read_loopback:
            if chan == self.CH_BROADCAST:
                reply_dict = self._read_text(timeout=timeout)
                if reply_dict is None:
                    six.print_(
                        "Warning reply_dict is None in FT_TEXT_TX() broadcast loopback"
                    )
                else:
                    if isinstance(reply_dict, dict):
                        reply_dict["GCprotocol"]["body"].update({"data": {}})
                        datar = reply_dict["GCprotocol"]["body"][self.RAWDATA]
                        if sys.version_info[0] < 3:
                            msg = "".join(datar).split("\x00")[0]
                        else:
                            msg = "".join(map(chr, datar)).split("\x00")[0]
                        reply_dict["GCprotocol"]["body"]["data"].update(
                            {"broadcast": msg}
                        )
                    else:
                        six.print_(
                            "Warning reply_dict without expected keys in FT_TEXT_TX() broadcast loopback"
                        )
            elif chan == self.client_id:
                reply_dict = self._read_text(timeout=timeout)
                # TODO
            else:
                # TODO
                pass
        return reply_dict

    def CMD_LDF_LIST(self):
        """get entire list of LDF names
        Not Yet Implemented

        Args:
            none

        Pre:
            CMD_SERVER_REG()
            CMD_LDF_DESC_AND_UPLOAD()
            CMD_LDF_PARSE()

        Post:

        Returns:
            array of names and descriptions (in a dict)

        Raises:
            None.
        """
        raise self.NotYetImplemented

    def CMD_LDF_DESC_AND_UPLOAD(self, filename, description):
        """describe the file and upload the contents
        Not Yet Implemented

        Args:
            none

        Pre:
            CMD_SERVER_REG()

        Post:

        Returns:
            None

        Raises:
            None.
        """
        #
        # ----------------------------------------------------------------------
        # pylint: disable=too-many-locals
        # ----------------------------------------------------------------------
        #
        # open the file, get it's total size
        raise self.NotYetImplemented

    def CMD_LDF_DELETE(self, filename):
        """delete
        Not Yet Implemented

        Args:
            filename

        Pre:
            CMD_SERVER_REG()

        Post:

        Returns:
            None.

        Raises:
            None.
        """
        raise self.NotYetImplemented

    def CMD_LDF_PARSE(self, filename):
        """delete
        Not Yet Implemented

        Args:
            filename

        Pre:
            CMD_SERVER_REG()
            CMD_LDF_DESC_AND_UPLOAD()

        Post:

        Returns:
            None.

        Raises:
            None.
        """
        raise self.NotYetImplemented

    def CMD_GET_LDF_INFO(self):
        """delete
        Not Yet Implemented

        Args:
            none

        Pre:
            CMD_SERVER_REG()
            CMD_LDF_DESC_AND_UPLOAD()
            CMD_LDF_PARSE()

        Post:

        Returns:
            None.

        Raises:
            None.
        """
        raise self.NotYetImplemented

    def CMD_GET_NODE_NAMES(self):
        """get entire list of LDF names
        Not Yet Implemented

        Args:
            none

        Pre:
            CMD_SERVER_REG()
            CMD_LDF_DESC_AND_UPLOAD()
            CMD_LDF_PARSE()

        Post:

        Returns:
            array of names and descriptions (in a dict)

        Raises:
            None.
        """
        raise self.NotYetImplemented

    def CMD_GET_NODE_SIGNALS(self, node_in):
        """get entire list of LDF names
        Not Yet Implemented

        Args:
            node

        Pre:
            CMD_SERVER_REG()
            CMD_LDF_DESC_AND_UPLOAD()
            CMD_LDF_PARSE()

        Post:

        Returns:
            array of names

        Raises:
            None.
        """
        raise self.NotYetImplemented

    def CMD_EMULATE_NODES(self, nodes_in):
        """get entire list of LDF names
        Not Yet Implemented

        Args:
            nodes array of dict

        Pre:
            CMD_SERVER_REG()
            CMD_LDF_DESC_AND_UPLOAD()
            CMD_LDF_PARSE()

        Post:

        Returns:
            None.

        Raises:
            None.
        """
        raise self.NotYetImplemented

    def CMD_GET_FRAMES(self, node_in):
        """get entire list of LDF names
        Not Yet Implemented

        Args:
            node str

        Pre:
            CMD_SERVER_REG()
            CMD_LDF_DESC_AND_UPLOAD()
            CMD_LDF_PARSE()

        Post:

        Returns:
            None.

        Raises:
            None.
        """
        raise self.NotYetImplemented

    def CMD_GET_FRAME_INFO(self, frame, id_in=None):
        """get entire list of LDF names
        Not Yet Implemented

        Args:
            frame str
            id int

        Pre:
            CMD_SERVER_REG()
            CMD_LDF_DESC_AND_UPLOAD()
            CMD_LDF_PARSE()

        Post:

        Returns:
            None.

        Raises:
            None.
        """
        raise self.NotYetImplemented

    def CMD_GET_SIGNAL_INFO(self, mysignal):
        """get entire list of LDF names
        Not Yet Implemented

        Args:
            mysignal

        Pre:
            CMD_SERVER_REG()
            CMD_LDF_DESC_AND_UPLOAD()
            CMD_LDF_PARSE()

        Post:

        Returns:
            None.

        Raises:
            None.
        """
        raise self.NotYetImplemented

    def CMD_GET_SIGNAL_DETAIL(self, mysignal):
        """get
        Not Yet Implemented

        Args:
            mysignal

        Pre:
            CMD_SERVER_REG()
            CMD_LDF_DESC_AND_UPLOAD()
            CMD_LDF_PARSE()

        Post:

        Returns:
            None.

        Raises:
            None.
        """
        raise self.NotYetImplemented

    def CMD_GET_ENCODING_INFO(self, encoding_name):
        """get
        Not Yet Implemented

        Args:
            name

        Pre:
            CMD_SERVER_REG()
            CMD_LDF_DESC_AND_UPLOAD()
            CMD_LDF_PARSE()

        Post:

        Returns:
            None.

        Raises:
            None.
        """
        raise self.NotYetImplemented

    def CMD_GET_SCHEDULES(self):
        """get sched
        Not Yet Implemented

        Args:
            none

        Pre:
            CMD_SERVER_REG()
            CMD_LDF_DESC_AND_UPLOAD()
            CMD_LDF_PARSE()

        Post:

        Returns:
            None.

        Raises:
            None.
        """
        raise self.NotYetImplemented

    def CMD_START_SCHEDULE(self, name):
        """get sched
        Not Yet Implemented

        Args:
            name

        Pre:
            CMD_SERVER_REG()
            CMD_LDF_DESC_AND_UPLOAD()
            CMD_LDF_PARSE()

        Post:

        Returns:
            None.

        Raises:
            None.
        """
        raise self.NotYetImplemented

    def CMD_STORE_DATA(self, frame, id_in=None, data_in=None):
        """store data
        Not Yet Implemented

        Args:
            none

        Pre:
            CMD_SERVER_REG()
            CMD_LDF_DESC_AND_UPLOAD()
            CMD_LDF_PARSE()

        Post:

        Returns:
            None.

        Raises:
            None.
        """
        raise self.NotYetImplemented

    def CMD_SAVE_SESSION(self, dst=GryphonProtocolSD.SD_LIN, id_in="123"):
        """

        Args:
            dst is either SD_LIN or SD_CNVT
            id as a string

        Pre:
            CMD_SERVER_REG()
            for LIN:
                CMD_LDF_DESC_AND_UPLOAD()
                CMD_LDF_PARSE()
            for CAN:
                CMD_READ_CNVT_CONFIG()

        Post:

        Returns:
            None.

        Raises:
            None.
        """
        # done 20190306
        databa = bytearray()
        if sys.version_info[0] < 3:
            databa.extend(id_in.ljust(32, "\0"))
        else:
            databa.extend(bytes(id_in.ljust(32, "\0"), encoding="ascii"))
        reply_dict = self._build_and_send_command(
            dst=dst, dstchan=0, cmd=self.BCMD_SAVE_SESSION, data=databa
        )
        return reply_dict

    def CMD_RESTORE_SESSION(self, dst=GryphonProtocolSD.SD_LIN, id_in="123"):
        """

        Args:
            dst is either SD_LIN or SD_CNVT
            id

        Pre:
            CMD_SERVER_REG()
            for LIN:
                CMD_LDF_DESC_AND_UPLOAD()
                CMD_LDF_PARSE()
            for CAN:
                CMD_READ_CNVT_CONFIG()

        Post:

        Returns:
            None.

        Raises:
            None.
        """
        # done 20190306
        databa = bytearray()
        if sys.version_info[0] < 3:
            databa.extend(id_in.ljust(32, "\0"))
        else:
            databa.extend(bytes(id_in.ljust(32, "\0"), encoding="ascii"))
        reply_dict = self._build_and_send_command(
            dst=dst, dstchan=0, cmd=self.BCMD_RESTORE_SESSION, data=databa
        )
        return reply_dict

    def CMD_CNVT_GET_VALUES(self, chan, dataa_in):
        """signal converter get values
        Not Yet Implemented

        Args:
            array

        Pre:
            CMD_SERVER_REG()

        Post:

        Returns:
            None.

        Raises:
            None.
        """
        raise self.NotYetImplemented

    def CMD_CNVT_GET_UNITS(self, chan, dataa_in):
        """signal converter get units
        Not Yet Implemented

        Args:
            array

        Pre:
            CMD_SERVER_REG()

        Post:

        Returns:
            None.

        Raises:
            None.
        """
        raise self.NotYetImplemented

    def CMD_CNVT_GET_NODE_SIGNALS(self, node_in):
        """get entire list of LDF names
        Not Yet Implemented

        Args:
            node

        Pre:
            CMD_SERVER_REG()
            CMD_LDF_DESC_AND_UPLOAD()
            CMD_LDF_PARSE()

        Post:

        Returns:
            array of names

        Raises:
            None.
        """
        raise self.NotYetImplemented

    def CMD_CNVT_SET_VALUES(self, chan, dataa_in):
        """signal converter set values
        Not Yet Implemented

        Args:
            array

        Pre:
            CMD_SERVER_REG()

        Post:

        Returns:
            None.

        Raises:
            None.
        """
        raise self.NotYetImplemented

    def CMD_READ_CNVT_CONFIG(self, filename):
        """signal converter CAN .dbc read config

        Args:
            filename of xml file in /gryphon/convert

        Pre:
            CMD_SERVER_REG()
            config file filename is already upload to BEACON using the BEACON web page

        Post:

        Returns:
            dictionary

        Raises:
            None.
        """
        # done 20190306
        # adjust filename if needed to point to the xml file
        config_filename = filename
        filename, file_extension = os.path.splitext(filename)
        if file_extension != ".xml":
            if file_extension.lower() == ".dbc":
                config_filename = filename + ".xml"
            elif file_extension == "":
                config_filename = filename + ".xml"
            else:
                raise self.IncorrectXMLConfigFilename(filename)

        databa = bytearray()
        if sys.version_info[0] < 3:
            databa.extend(config_filename)
        else:
            databa.extend(bytes(config_filename, encoding="ascii"))
        databa.extend([0])
        # filnamelength = len(config_filename)
        # reply_dict = self._build_and_send_command(dst=self.SD_CNVT, dstchan=0, cmd=self.BCMD_READ_CNVT_CONFIG, data=databa, unusual_length = filnamelength + 4)
        reply_dict = self._build_and_send_command(
            dst=self.SD_CNVT, dstchan=0, cmd=self.BCMD_READ_CNVT_CONFIG, data=databa
        )

        return reply_dict

    def CMD_CNVT_GET_MSG_NAMES(self):
        """signal converter CAN .dbc get message names

        Args:
            none.

        Pre:
            CMD_SERVER_REG()
            CMD_READ_CNVT_CONFIG(filename)
            config file filename is already upload to BEACON using the BEACON web page

        Post:

        Returns:
            dictionary that contains an array of message names

        Raises:
            None.
        """
        # done 20190306
        reply_dict = self._build_and_send_command(
            dst=self.SD_CNVT, dstchan=0, cmd=self.BCMD_CNVT_GET_MSG_NAMES, data=None
        )
        if sys.version_info[0] < 3:
            nids = (ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][8]) * 256) + ord(
                reply_dict["GCprotocol"]["body"][self.RAWDATA][9]
            )
            reply_dict["GCprotocol"]["body"].update({"data": {}})
            reply_dict["GCprotocol"]["body"]["data"].update({"number": nids})
            reply_dict["GCprotocol"]["body"]["data"].update({"names": []})
            index = 10
            for _ in range(0, nids):
                name = {}
                frame_id_length = ord(
                    reply_dict["GCprotocol"]["body"][self.RAWDATA][index]
                )
                name["frame_id_length"] = frame_id_length
                index += 1
                frame_id = 0
                for n in range(frame_id_length - 1, 0, -1):
                    frame_id += ord(
                        reply_dict["GCprotocol"]["body"][self.RAWDATA][index]
                    ) * (256 * n)
                    index += 1
                frame_id += ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][index])
                index += 1
                name["frame_id"] = frame_id
                end = index + reply_dict["GCprotocol"]["body"][self.RAWDATA][
                    index:
                ].index(
                    "\x00"
                )  # find first null at end of C string
                name["message_name"] = "".join(
                    reply_dict["GCprotocol"]["body"][self.RAWDATA][index:end]
                )
                index = end + 1
                reply_dict["GCprotocol"]["body"]["data"]["names"].append(name)
        else:
            nids = (
                reply_dict["GCprotocol"]["body"][self.RAWDATA][8] * 256
            ) + reply_dict["GCprotocol"]["body"][self.RAWDATA][9]
            reply_dict["GCprotocol"]["body"].update({"data": {}})
            reply_dict["GCprotocol"]["body"]["data"].update({"number": nids})
            reply_dict["GCprotocol"]["body"]["data"].update({"names": []})
            index = 10
            for _ in range(0, nids):
                name = {}
                frame_id_length = reply_dict["GCprotocol"]["body"][self.RAWDATA][index]
                name["frame_id_length"] = frame_id_length
                index += 1
                frame_id = 0
                for n in range(frame_id_length - 1, 0, -1):
                    frame_id += reply_dict["GCprotocol"]["body"][self.RAWDATA][
                        index
                    ] * (256 * n)
                    index += 1
                frame_id += reply_dict["GCprotocol"]["body"][self.RAWDATA][index]
                index += 1
                name["frame_id"] = frame_id
                end = index + reply_dict["GCprotocol"]["body"][self.RAWDATA][
                    index:
                ].index(
                    0
                )  # find first null at end of C string
                name["message_name"] = "".join(
                    map(chr, reply_dict["GCprotocol"]["body"][self.RAWDATA][index:end])
                )
                index = end + 1
                reply_dict["GCprotocol"]["body"]["data"]["names"].append(name)

        return reply_dict

    def CMD_CNVT_GET_SIG_NAMES(self, message_name):
        """signal converter CAN .dbc get signal names

        Args:
            message_name as a string returned from CMD_CNVT_GET_MSG_NAMES()

        Pre:
            CMD_SERVER_REG()
            CMD_READ_CNVT_CONFIG(filename)
            CMD_CNVT_GET_MSG_NAMES()
            config file filename is already upload to BEACON using the BEACON web page

        Post:

        Returns:
            dictionary that contains an array of signal names

        Raises:
            None.
        """
        # done 20190306
        databa = bytearray()
        if sys.version_info[0] < 3:
            databa.extend(message_name)
            databa.extend([0])
            reply_dict = self._build_and_send_command(
                dst=self.SD_CNVT,
                dstchan=0,
                cmd=self.BCMD_CNVT_GET_SIG_NAMES,
                data=databa,
            )
            nsigs = (
                ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][8]) * 256
            ) + ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][9])
            reply_dict["GCprotocol"]["body"].update({"data": {}})
            reply_dict["GCprotocol"]["body"]["data"].update({"number": nsigs})
            reply_dict["GCprotocol"]["body"]["data"].update({"signals": []})
            index = 10
            for _ in range(0, nsigs):
                signaldict = {}
                end = index + reply_dict["GCprotocol"]["body"][self.RAWDATA][
                    index:
                ].index(
                    "\x00"
                )  # find first null at end of C string
                signaldict["signal_name"] = "".join(
                    reply_dict["GCprotocol"]["body"][self.RAWDATA][index:end]
                )
                index = end + 1
                reply_dict["GCprotocol"]["body"]["data"]["signals"].append(signaldict)
        else:
            databa.extend(bytes(message_name, encoding="ascii"))
            databa.extend([0])
            reply_dict = self._build_and_send_command(
                dst=self.SD_CNVT,
                dstchan=0,
                cmd=self.BCMD_CNVT_GET_SIG_NAMES,
                data=databa,
            )
            nsigs = (
                reply_dict["GCprotocol"]["body"][self.RAWDATA][8] * 256
            ) + reply_dict["GCprotocol"]["body"][self.RAWDATA][9]
            reply_dict["GCprotocol"]["body"].update({"data": {}})
            reply_dict["GCprotocol"]["body"]["data"].update({"number": nsigs})
            reply_dict["GCprotocol"]["body"]["data"].update({"signals": []})
            index = 10
            for _ in range(0, nsigs):
                signaldict = {}
                end = index + reply_dict["GCprotocol"]["body"][self.RAWDATA][
                    index:
                ].index(
                    0
                )  # find first null at end of C string
                signaldict["signal_name"] = "".join(
                    map(chr, reply_dict["GCprotocol"]["body"][self.RAWDATA][index:end])
                )
                index = end + 1
                reply_dict["GCprotocol"]["body"]["data"]["signals"].append(signaldict)

        return reply_dict

    def CMD_CNVT_REQ_VALUES(self, chan, signal_list):
        """signal converter CAN .dbc get signal names

        Args:
            chan, 1 <= chan <= n_channels
            signal_list as a list of dictionaries holding
                signal_list['flag'] - (optional) default = 1, range = (1,2,3,4)
                signal_list['value'] - (optional) default = 0
                signal_list['signal_names'][n] as returned from CMD_CNVT_GET_SIG_NAMES()

        Pre:
            CMD_SERVER_REG()
            CMD_READ_CNVT_CONFIG(filename)
            CMD_CNVT_GET_MSG_NAMES()
            CMD_CNVT_GET_SIG_NAMES()
            config file filename is already upload to BEACON using the BEACON web page

        Post:

        Returns:
            dictionary that contains an array of

        Raises:
            ChannelNotValid(chan)
            SignalNameNotFound(signal_list)
        """
        # done 20190306
        if chan == 0:
            raise self.ChannelNotValid(chan)

        if "signal_names" not in signal_list:
            raise self.SignalNameNotFound(signal_list)

        databa = bytearray()
        nsigs = len(signal_list["signal_names"])
        databa.extend([nsigs])  # numb of signals
        if "flag" in signal_list:
            databa.extend([signal_list["flag"]])  # flag
        else:
            databa.extend([1])  # default flag 0x00
        if "value" in signal_list:
            val1 = (signal_list["value"] & 0xFF00) >> 8
            val2 = signal_list["value"] & 0x00FF
            databa.extend([val1, val2])  # value
        else:
            databa.extend([0, 0])  # default value 0x0000

        if sys.version_info[0] < 3:
            for item in signal_list["signal_names"]:
                databa.extend(item)
                databa.extend([0])  # null terminated string

            reply_dict = self._build_and_send_command(
                dst=self.SD_CNVT,
                dstchan=chan,
                cmd=self.BCMD_CNVT_REQ_VALUES,
                data=databa,
            )
            signal_request_index = ord(
                reply_dict["GCprotocol"]["body"][self.RAWDATA][8]
            )
            nunits = ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][9])
            reply_dict["GCprotocol"]["body"].update({"data": {}})
            reply_dict["GCprotocol"]["body"]["data"].update(
                {"signal_request_index": signal_request_index}
            )
            reply_dict["GCprotocol"]["body"]["data"].update({"number": nunits})
            reply_dict["GCprotocol"]["body"]["data"].update({"units": []})
            index = 10
            for _ in range(0, nunits):
                units = ""
                end = index + reply_dict["GCprotocol"]["body"][self.RAWDATA][
                    index:
                ].index(
                    "\x00"
                )  # find first null at end of C string
                units = "".join(
                    reply_dict["GCprotocol"]["body"][self.RAWDATA][index:end]
                )
                index = end + 1
                reply_dict["GCprotocol"]["body"]["data"]["units"].append(units)
        else:
            for item in signal_list["signal_names"]:
                databa.extend(bytes(item, encoding="ascii"))
                databa.extend([0])  # null terminated string

            reply_dict = self._build_and_send_command(
                dst=self.SD_CNVT,
                dstchan=chan,
                cmd=self.BCMD_CNVT_REQ_VALUES,
                data=databa,
            )
            signal_request_index = reply_dict["GCprotocol"]["body"][self.RAWDATA][8]
            nunits = reply_dict["GCprotocol"]["body"][self.RAWDATA][9]
            reply_dict["GCprotocol"]["body"].update({"data": {}})
            reply_dict["GCprotocol"]["body"]["data"].update(
                {"signal_request_index": signal_request_index}
            )
            reply_dict["GCprotocol"]["body"]["data"].update({"number": nunits})
            reply_dict["GCprotocol"]["body"]["data"].update({"units": []})
            index = 10
            for _ in range(0, nunits):
                units = ""
                end = index + reply_dict["GCprotocol"]["body"][self.RAWDATA][
                    index:
                ].index(
                    0
                )  # find first null at end of C string
                units = "".join(
                    map(chr, reply_dict["GCprotocol"]["body"][self.RAWDATA][index:end])
                )
                index = end + 1
                reply_dict["GCprotocol"]["body"]["data"]["units"].append(units)

        return reply_dict

    # 20190115
    def CMD_MSGRESP_ADD(self, chan, dataa_in):
        """responder

        see also FT_MISC_TX()

        Args:
            chan, 1 <= chan <= n_channels
            dataa_in["filter_flag"] - (optional) default is GryphonProtocolFilterFlags().FILTER_FLAG_ACTIVE
            dataa_in["old_handle"] - (optional) handle of a response to replace
            dataa_in["action_code"] - (optional) one of GryphonProtocolMSGRESPActions
            dataa_in["action_flags"] - (optional) one of GryphonProtocolMSGRESPActions
            dataa_in["action_value"] - (optional) number of milliseconds or number of messages, int
            dataa_in["filter_blocks"] - [] list of filter blocks
                ['byte_offset'] - int
                ['data_type'] - one of class GryphonProtocolFilterDataType()
                ['operator'] - one of class GryphonProtocolFilterCondition()
                ['pattern'] - if operator is BIT_FIELD_CHECK, [] list
                ['mask'] - if operator is BIT_FIELD_CHECK, [] list
                ['value'] - for VALUE operators, [] list
                ['bit_mask'] - for DIGI operators, [] list
            dataa_in["response_blocks"] - [] list of response blocks
                ['framehdr']['src'] - (optional)
                ['framehdr']['srcchan'] - (optional)
                ['framehdr']['dst'] -
                ['framehdr']['dstchan'] -
                ['framehdr']['frametype'] - (optional), default is FT_DATA
                ['framehdr']['flag_dont_wait'] - (optional), default is False
                ['framehdr']['flag_send_after'] - (optional), default is False
                ['body']['data']['hdrlen'] - (optional)
                ['body']['data']['hdrbits'] - (optional)
                ['body']['data']['datalen'] - (optional)
                ['body']['data']['extralen'] - (optional)
                ['body']['data']['mode'] - (optional)
                ['body']['data']['pri'] - (optional)
                ['body']['data']['status'] - (optional)
                ['body']['data']['timestamp'] - (optional)
                ['body']['data']['context'] - (optional)
                ['body']['data']['hdr'] - [] list of header bytes
                ['body']['data']['data'] - (optional) [] list of data bytes
                ['body']['data']['extra'] - (optional) [] list of extra bytes
                ['body']['text'] - (optional), for FT_TEXT message

        Pre:
            CMD_SERVER_REG()

        Post:

        Returns:

        Raises:
            ChannelNotValid(chan)
        """
        #
        # ----------------------------------------------------------------------
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-arguments
        # ----------------------------------------------------------------------
        #
        # done 20190103
        if chan == 0:
            raise self.ChannelNotValid(chan)

        # flags
        if ("filter_flag" in dataa_in) and (
            dataa_in["filter_flag"] == GryphonProtocolFilterFlags.FILTER_FLAG_INACTIVE
        ):
            flags = GryphonProtocolFilterFlags.FILTER_FLAG_INACTIVE  # default
        else:
            flags = GryphonProtocolFilterFlags.FILTER_FLAG_ACTIVE  # default

        # n filter blocks
        if "filter_blocks" not in dataa_in:
            raise self.FilterBlocksNotFound
        nfilter_blocks = len(dataa_in["filter_blocks"])

        # n response blocks
        if "response_blocks" not in dataa_in:
            raise self.RespBlocksNotFound()
        nresp_blocks = len(dataa_in["response_blocks"])

        # old_handle
        if "old_handle" in dataa_in:
            old_handle = dataa_in["old_handle"]
        else:
            old_handle = 0  # default

        # action_code default is GryphonProtocolMSGRESPActions.FR_RESP_AFTER_EVENT
        if "action_code" in dataa_in:
            # must be one and only one of these
            if dataa_in["action_code"] not in (
                GryphonProtocolMSGRESPActions.FR_RESP_AFTER_EVENT,
                GryphonProtocolMSGRESPActions.FR_RESP_AFTER_PERIOD,
                GryphonProtocolMSGRESPActions.FR_IGNORE_DURING_PER,
            ):
                raise self.ActionNotValid(dataa_in["action_code"])
            action_code = dataa_in["action_code"]
        else:
            action_code = GryphonProtocolMSGRESPActions.FR_RESP_AFTER_EVENT

        # action_flags default is GryphonProtocolMSGRESPActions.FR_RESP_AFTER_EVENT
        if "action_flag" in dataa_in:
            if dataa_in["action_flag"] not in (
                0,
                GryphonProtocolMSGRESPActions.FR_PERIOD_MSGS,
                GryphonProtocolMSGRESPActions.FR_DELETE,
                GryphonProtocolMSGRESPActions.FR_DEACT_ON_EVENT,
                GryphonProtocolMSGRESPActions.FR_DEACT_AFTER_PER,
            ):
                raise self.ActionNotValid(dataa_in["action_flag"])
            action_code |= dataa_in["action_flag"]

        # break into 2 bytes
        action_value1 = 0  # default
        action_value2 = 0  # default
        if "action_value" in dataa_in:
            action_value1 = (dataa_in["action_value"] & 0xFF00) >> 8
            action_value2 = (dataa_in["action_value"] & 0x00FF) >> 0

        # implement action_value, action_time_value, action_message_counter_value
        if "action_time_value" in dataa_in:
            if (
                not dataa_in["action_flag"]
                & GryphonProtocolMSGRESPActions.FR_PERIOD_MSGS
            ):
                raise self.ActionNotValid(dataa_in["action_time_value"])
            if "action_value" in dataa_in:
                if dataa_in["action_value"] != dataa_in["action_time_value"]:
                    raise self.ActionNotValid(dataa_in["action_time_value"])
            action_value1 = (dataa_in["action_time_value"] & 0xFF00) >> 8
            action_value2 = (dataa_in["action_time_value"] & 0x00FF) >> 0
        if "action_message_counter_value" in dataa_in:
            if (
                not dataa_in["action_flag"]
                & GryphonProtocolMSGRESPActions.FR_PERIOD_MSGS
            ):
                raise self.ActionNotValid(dataa_in["action_message_counter_value"])
            if "action_value" in dataa_in:
                if dataa_in["action_value"] != dataa_in["action_message_counter_value"]:
                    raise self.ActionNotValid(dataa_in["action_message_counter_value"])
            action_value1 = (dataa_in["action_message_counter_value"] & 0xFF00) >> 8
            action_value2 = (dataa_in["action_message_counter_value"] & 0x00FF) >> 0

        databa = bytearray()
        databa.extend(
            [flags, nfilter_blocks, nresp_blocks, old_handle]
        )  # flags, #filter blocks, #resps, oldhandle
        databa.extend([action_code, 0, action_value1, action_value2])

        filters = bytearray()
        # filter blocks
        for block in dataa_in["filter_blocks"]:

            if "byte_offset" not in block:
                raise self.ByteOffsetNotFound
            # break into 2 bytes
            bo1 = (block["byte_offset"] & 0xFF00) >> 8
            bo2 = (block["byte_offset"] & 0x00FF) >> 0
            filters.extend([bo1, bo2])

            field_length = 0
            if "operator" not in block:
                raise self.OperatorNotFound
            if block["operator"] == GryphonProtocolFilterCondition.BIT_FIELD_CHECK:
                if "pattern" not in block:
                    raise self.PatternNotFound
                if "mask" not in block:
                    raise self.MaskNotFound
                if len(block["pattern"]) != len(block["mask"]):
                    raise self.LengthsNotEqual(block["pattern"], block["mask"])

                field_length = len(block["pattern"])
                pattern_mask_length = len(block["pattern"]) + len(block["mask"])

            elif (
                (block["operator"] == GryphonProtocolFilterCondition.DIG_LOW_TO_HIGH)
                or (block["operator"] == GryphonProtocolFilterCondition.DIG_HIGH_TO_LOW)
                or (block["operator"] == GryphonProtocolFilterCondition.DIG_TRANSITION)
            ):

                if "bit_mask" not in block:
                    raise self.BitMaskNotFound

                field_length = len(block["bit_mask"])

            else:

                if "value" not in block:
                    raise self.ValueNotFound

                field_length = len(block["value"])

            # break into 2 bytes
            le1 = (field_length & 0xFF00) >> 8
            le2 = (field_length & 0x00FF) >> 0
            filters.extend([le1, le2])

            values = dir(GryphonProtocolFilterDataType)
            # filter out all of the __x__ attributes
            values[:] = [x for x in values if "__" not in x]
            filtervalues = []
            # get the actual values of all of the commands, using the attribute names
            filtervalues.extend(
                [getattr(GryphonProtocolFilterDataType, x) for x in values]
            )
            if block["data_type"] not in filtervalues:
                raise self.ValueNotInFilterDataType(block["data_type"])

            filters.extend([block["data_type"]])
            filters.extend([block["operator"]])
            filters.extend([0, 0])  # reserved

            if block["operator"] == GryphonProtocolFilterCondition.BIT_FIELD_CHECK:
                filters.extend(block["pattern"])
                filters.extend(block["mask"])
                filters.extend(self._padding(pattern_mask_length))  # padding
            elif (
                (block["operator"] == GryphonProtocolFilterCondition.DIG_LOW_TO_HIGH)
                or (block["operator"] == GryphonProtocolFilterCondition.DIG_HIGH_TO_LOW)
                or (block["operator"] == GryphonProtocolFilterCondition.DIG_TRANSITION)
            ):
                filters.extend(block["bit_mask"])
                filters.extend(self._padding(field_length))  # padding
            else:
                filters.extend(block["value"])
                filters.extend(self._padding(field_length))  # padding

        databa.extend(filters)

        gcframes = bytearray()
        # response blocks
        for block in dataa_in["response_blocks"]:
            if "framehdr" not in block:
                raise self.FrameHdrNotFound

            if "src" in block["framehdr"]:
                src = block["framehdr"]["src"]
            else:
                src = GryphonProtocolSD.SD_CLIENT

            if "srcchan" in block["framehdr"]:
                srcchan = block["framehdr"]["srcchan"]
            else:
                srcchan = self.client_id

            if "dst" not in block["framehdr"]:
                raise self.FrameHdrNotFound
            if "dstchan" not in block["framehdr"]:
                raise self.FrameHdrNotFound
            dst = block["framehdr"]["dst"]
            dstchan = block["framehdr"]["dstchan"]

            gcframes.extend([src, srcchan, dst, dstchan])  # src, srchan, dst, dstchan

            # default FT_DATA
            if "frametype" in block["framehdr"]:
                # TODO create defines to replace constants
                frametype = block["framehdr"]["frametype"] & 0x3F
            else:
                frametype = block["framehdr"][
                    "frametype"
                ] = GryphonProtocolFT.FT_DATA  # default

            if "frametype_with_flags" in block["framehdr"]:
                frametype_raw = block["framehdr"]["frametype_with_flags"]
            else:
                frametype_raw = frametype

            if "flag_dont_wait" in block["framehdr"]:
                if block["framehdr"]["flag_dont_wait"]:
                    # TODO create defines to replace constants
                    frametype_raw |= 0x80  # dont wait for a response
            if "flag_send_after" in block["framehdr"]:
                if block["framehdr"]["flag_send_after"]:
                    # TODO create defines to replace constants
                    frametype_raw |= 0x40  # send out this command after all responses

            if "body" not in block:
                raise self.BodyNotFound

            if frametype == GryphonProtocolFT.FT_DATA:

                if "data" not in block["body"]:
                    raise self.DataNotFound

                data_in = block["body"]["data"]

                # hdrlen
                # %%%WARNING: must compute hdrlen before doing hdr[]
                hdrlen = None
                if "hdrlen" in data_in:
                    if isinstance(data_in["hdrlen"], six.integer_types):
                        hdrlen = data_in["hdrlen"]
                    else:
                        # TODO
                        raise self.ValueOutOfRange(data_in["hdrlen"])

                # hdr
                if "hdr" not in data_in:
                    raise self.HdrNotFound()

                hdr = []
                if isinstance(data_in["hdr"], (list, bytearray)):
                    if hdrlen is not None:
                        # only use hdrlen number of elems from hdr[]
                        maxhdr = min(hdrlen, len(data_in["hdr"]))
                        for ind in range(0, maxhdr):
                            hdr.append(data_in["hdr"][ind])
                    else:
                        hdrlen = len(data_in["hdr"])
                        hdr = data_in["hdr"]
                elif isinstance(data_in["hdr"], int):
                    if hdrlen is None:
                        raise self.HdrLenNotFound()
                    # split hdr into hdrlen number of bytes
                    for ind in range(0, hdrlen):
                        mask = 0x00FF << (8 * ind)
                        num = data_in["hdr"] * mask
                        mybyte = num >> (8 * ind)
                        hdr.append(mybyte)
                    # reverse the list
                    hdr.reverse()
                else:
                    raise self.HdrNotFound(data_in["hdr"])

                # hdrbits
                hdrbits = 11  # CANbus 11-bit header, default
                if "hdrbits" in data_in:
                    hdrbits = data_in["hdrbits"]
                else:
                    if hdrlen == 1:  # LINbus header
                        hdrbits = 8
                    elif hdrlen == 4:  # CANbus 29-bit header
                        hdrbits = 29
                    else:
                        hdrbits = 11  # CANbus 11-bit header, default

                # datalen
                # %%%WARNING: must compute datalen before doing data[]
                datalen = None
                if "datalen" in data_in:
                    if isinstance(data_in["datalen"], six.integer_types):
                        datalen = data_in["datalen"]
                    else:
                        raise self.ValueOutOfRange(data_in["datalen"])
                else:
                    if "data" in data_in:
                        datalen = len(data_in["data"])
                    else:
                        datalen = 0  # default

                # convert into two bytes
                datalen1 = (datalen & 0xFF00) >> 8
                datalen2 = (datalen & 0x00FF) >> 0

                # data
                data = []
                if "data" in data_in:
                    if isinstance(data_in["data"], (list, bytearray)):
                        maxdata = min(datalen, len(data_in["data"]))
                        for ind in range(0, maxdata):
                            data.append(data_in["data"][ind])
                    else:
                        # is single int
                        data.append(data_in["data"])

                # extralen
                # %%%WARNING: must compute extralen before doing extra[]
                if "extralen" in data_in:
                    if isinstance(data_in["extralen"], six.integer_types):
                        extralen = data_in["extralen"]
                    else:
                        # TODO
                        raise self.ExtraLenNotFound()
                else:
                    if "extra" in data_in:
                        extralen = len(data_in["extra"])
                    else:
                        extralen = 0  # default

                # extra
                extra = None
                if "extra" in data_in:
                    if isinstance(data_in["extra"], (list, bytearray)):
                        extra = []
                        maxextra = min(extralen, len(data_in["extra"]))
                        for ind in range(0, maxextra):
                            extra.append(data_in["extra"][ind])
                    else:
                        # is single int
                        extra = []
                        extra.append(data_in["extra"])

                if "pri" in data_in:
                    pri = data_in["pri"]
                else:
                    pri = 0  # default

                if "status" in data_in:
                    status = data_in["status"]
                else:
                    status = 0  # default

                if "mode" in data_in:
                    mode = data_in["mode"]
                else:
                    mode = 0  # default

                if frametype == GryphonProtocolFT.FT_DATA:
                    if (data is None) and (extra is None):
                        msglen = len(hdr) + 16
                    elif (data is not None) and (extra is None):
                        msglen = len(hdr) + len(data) + 16
                    elif (data is None) and (extra is not None):
                        msglen = len(hdr) + len(extra) + 16
                    else:
                        msglen = len(hdr) + len(data) + len(extra) + 16
                elif frametype == GryphonProtocolFT.FT_EVENT:
                    # TODO implement FT_EVENT for CMD_MSGRESP_ADD()
                    raise self.ValueNotValid(block["framehdr"]["frametype"])
                elif frametype == GryphonProtocolFT.FT_MISC:
                    # TODO implement FT_MISC for CMD_MSGRESP_ADD()
                    raise self.ValueNotValid(block["framehdr"]["frametype"])
                elif frametype == GryphonProtocolFT.FT_TEXT:
                    # TODO implement FT_TEXT for CMD_MSGRESP_ADD()
                    raise self.ValueNotValid(block["framehdr"]["frametype"])
                elif frametype == GryphonProtocolFT.FT_SIG:
                    # TODO implement FT_SIG for CMD_MSGRESP_ADD()
                    raise self.ValueNotValid(block["framehdr"]["frametype"])
                else:
                    raise self.ValueNotInFT(block["framehdr"]["frametype"])

                msglen1 = (msglen & 0xFF00) >> 8
                msglen2 = (msglen & 0x00FF) >> 0

                # NOTE: we will need to go back and calculate the message len when all done
                gcframes.extend(
                    [msglen1, msglen2, frametype_raw, 0]
                )  # data len, frame type, rsvd
                gcframes.extend(
                    [hdrlen, hdrbits, datalen1, datalen2]
                )  # BEACON data header, hdrlen, hdrbits, data len
                gcframes.extend(
                    [extralen, mode, pri, status]
                )  # BEACON data header, extralen, mode, pri, status

                timestamp = []
                if "timestamp" in data_in:
                    if isinstance(data_in["timestamp"], list):
                        timestamp = data_in["timestamp"]
                    else:
                        # turn int into a list
                        # TODO
                        timestamp.append(
                            ((data_in["timestamp"] & 0xFF000000) >> 24) & 0xFF
                        )
                        timestamp.append(
                            ((data_in["timestamp"] & 0x00FF0000) >> 16) & 0xFF
                        )
                        timestamp.append(
                            ((data_in["timestamp"] & 0x0000FF00) >> 8) & 0xFF
                        )
                        timestamp.append(
                            ((data_in["timestamp"] & 0x000000FF) >> 0) & 0xFF
                        )
                else:
                    timestamp = [0, 0, 0, 0]  # default

                gcframes.extend(timestamp)  # timestamp

                if "context" in data_in:
                    context = data_in["context"]
                else:
                    context = self.cmd_context  # default

                gcframes.extend([context, 0, 0, 0])  # context, reserved
                gcframes.extend(hdr)  # msg header
                if data is not None:
                    gcframes.extend(data)  # msg data
                if extra is not None:
                    gcframes.extend(extra)  # msg extra
                # padding
                lena = len(hdr) + len(data)
                gcframes.extend(self._padding(lena))  # padding

            elif frametype == GryphonProtocolFT.FT_TEXT:

                if "text" not in block["body"]:
                    raise self.TextNotFound

                lena = len(block["body"]["text"])
                gcframes.extend(block["body"]["text"])
                gcframes.extend(self._padding(lena))  # padding
            else:
                raise self.ValueNotInFT(block["framehdr"]["frametype"])

        databa.extend(gcframes)

        reply_dict = self._build_and_send_command(
            dst=self.SD_RESP, dstchan=chan, cmd=self.BCMD_MSGRESP_ADD, data=databa
        )
        if sys.version_info[0] < 3:
            reply_dict.update(
                {
                    "response_handle": ord(
                        reply_dict["GCprotocol"]["body"][self.RAWDATA][8]
                    )
                }
            )
            reply_dict["GCprotocol"]["body"].update({"data": {}})
            reply_dict["GCprotocol"]["body"]["data"].update(
                {
                    "response_handle": ord(
                        reply_dict["GCprotocol"]["body"][self.RAWDATA][8]
                    )
                }
            )
        else:
            reply_dict.update(
                {"response_handle": reply_dict["GCprotocol"]["body"][self.RAWDATA][8]}
            )
            reply_dict["GCprotocol"]["body"].update({"data": {}})
            reply_dict["GCprotocol"]["body"]["data"].update(
                {"response_handle": reply_dict["GCprotocol"]["body"][self.RAWDATA][8]}
            )
        return reply_dict

    def CMD_MSGRESP_MODIFY(self, chan, handle, action):
        """responder

        Args:
            chan - 1 <= chan <= n_channels
            handle -
            action -

        Pre:
            CMD_SERVER_REG()
            CMD_MSGRESP_ADD()

        Post:

        Returns:
            None.

        Raises:
            None.
        """
        # done 20190103

        if action not in (
            GryphonProtocolMSGRESPActions.MSGRESP_DELETE_RESPONSE,
            GryphonProtocolMSGRESPActions.MSGRESP_ACTIVATE_RESPONSE,
            GryphonProtocolMSGRESPActions.MSGRESP_DEACTIVATE_RESPONSE,
        ):
            raise self.ActionNotValid(action)

        databa = bytearray()
        databa.extend([handle, action])
        resp_dict = self._build_and_send_command(
            dst=self.SD_RESP, dstchan=chan, cmd=self.BCMD_MSGRESP_MODIFY, data=databa
        )
        return resp_dict

    def CMD_MSGRESP_GET_HANDELS(self, chan=0):
        """responder

        Args:
            array

        Pre:
            CMD_SERVER_REG()

        Post:
            None.

        Returns:
            dict containing a list in reply_dict["GCprotocol"]["body"]["data"]["response_handles"]

        Raises:
            None.
        """
        # done 20190103
        reply_dict = self._build_and_send_command(
            dst=self.SD_RESP, dstchan=chan, cmd=self.BCMD_MSGRESP_GET_HANDLES, data=None
        )
        reply_dict["GCprotocol"]["body"].update({"data": {}})
        msgresp_array = []
        if sys.version_info[0] < 3:
            nresponses = ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][8])
            for i in range(0, nresponses):
                msgresp_array.append(
                    ord(reply_dict["GCprotocol"]["body"][self.RAWDATA][9 + i])
                )
        else:
            nresponses = reply_dict["GCprotocol"]["body"][self.RAWDATA][8]
            for i in range(0, nresponses):
                msgresp_array.append(
                    reply_dict["GCprotocol"]["body"][self.RAWDATA][9 + i]
                )
        reply_dict["GCprotocol"]["body"]["data"].update(
            {"response_handles": msgresp_array}
        )
        return reply_dict

    def CMD_MSGRESP_GET(self, response_handle):
        """responder

        Args:
            int response_handle

        Pre:
            CMD_SERVER_REG()
            CMD_MSGRESP_ADD()

        Post:
            None.

        Returns:
            dict

        Raises:
            None.
        """
        # done 20190103
        #
        # ----------------------------------------------------------------------
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        # ----------------------------------------------------------------------
        #
        databa = bytearray()
        databa.extend([response_handle])
        reply_dict = self._build_and_send_command(
            dst=self.SD_RESP, dstchan=0, cmd=self.BCMD_MSGRESP_GET, data=databa
        )
        reply_dict["GCprotocol"]["body"].update({"data": {}})
        datar = reply_dict["GCprotocol"]["body"][self.RAWDATA]
        msgresp_dict = {}
        if sys.version_info[0] < 3:
            if ord(datar[8]) & GryphonProtocolFilterFlags.FILTER_FLAG_ACTIVE:
                filter_flag = GryphonProtocolFilterFlags.FILTER_FLAG_ACTIVE
            else:
                filter_flag = GryphonProtocolFilterFlags.FILTER_FLAG_INACTIVE
            msgresp_dict.update({"filter_flag": filter_flag})

            nfilter_blocks = ord(datar[9])
            nresp_blocks = ord(datar[10])

            old_handle = ord(datar[11])
            msgresp_dict.update({"old_handle": old_handle})

            # action
            action = ord(datar[12])  # raw action byte
            msgresp_dict.update({"action": action})  # raw action byte
            # action_code
            action_code = ord(datar[12]) & (
                GryphonProtocolMSGRESPActions.FR_RESP_AFTER_EVENT
                | GryphonProtocolMSGRESPActions.FR_RESP_AFTER_PERIOD
                | GryphonProtocolMSGRESPActions.FR_IGNORE_DURING_PER
            )
            msgresp_dict.update({"action_code": action_code})
            # action_flag
            action_flag = ord(datar[12]) & (
                GryphonProtocolMSGRESPActions.FR_PERIOD_MSGS
                | GryphonProtocolMSGRESPActions.FR_DELETE
                | GryphonProtocolMSGRESPActions.FR_DEACT_ON_EVENT
                | GryphonProtocolMSGRESPActions.FR_DEACT_AFTER_PER
            )
            msgresp_dict.update({"action_flag": action_flag})

            # TODO
            # if ord(datar[12]) & (GryphonProtocolMSGRESPActions.FR_DELETE):
            # if ord(datar[12]) & (GryphonProtocolMSGRESPActions.FR_DEACT_ON_EVENT):
            # if ord(datar[12]) & (GryphonProtocolMSGRESPActions.FR_DEACT_AFTER_PER):

            # reserverd datar[13]

            # action_value, action_time_value, action_message_counter_value
            action_value = (ord(datar[14]) * 256) + ord(datar[15])
            msgresp_dict.update({"action_value": action_value})
            if ord(datar[12]) & GryphonProtocolMSGRESPActions.FR_PERIOD_MSGS:
                msgresp_dict.update({"action_message_counter_value": action_value})
            else:
                msgresp_dict.update({"action_time_value": action_value})

            # FILTER blocks
            msgresp_dict.update({"filter_blocks": []})
            ind = 16
            for _ in range(0, nfilter_blocks):
                blk = {}
                byte_offset = (ord(datar[ind]) * 256) + ord(datar[ind + 1])
                blk.update({"byte_offset": byte_offset})
                ind += 2

                field_length = (ord(datar[ind]) * 256) + ord(datar[ind + 1])
                ind += 2

                data_type = ord(datar[ind])
                blk.update({"data_type": data_type})
                ind += 1

                operator = ord(datar[ind])
                blk.update({"operator": operator})
                ind += 1

                # reserved
                ind += 2

                if operator == GryphonProtocolFilterCondition.BIT_FIELD_CHECK:
                    plist = []
                    for _ in range(0, field_length):
                        plist.append(ord(datar[ind]))
                        ind += 1
                    blk.update({"pattern": plist})
                    mlist = []
                    for _ in range(0, field_length):
                        mlist.append(ord(datar[ind]))
                        ind += 1
                    blk.update({"mask": mlist})

                    # here have to make sure we calculate to jump over any padding
                    ind += len(self._padding(field_length * 2))

                elif operator in (
                    GryphonProtocolFilterCondition.DIG_LOW_TO_HIGH,
                    GryphonProtocolFilterCondition.DIG_HIGH_TO_LOW,
                    GryphonProtocolFilterCondition.DIG_TRANSITION,
                ):
                    bmlist = []
                    for _ in range(0, field_length):
                        bmlist.append(ord(datar[ind]))
                        ind += 1
                    blk.update({"bit_mask": bmlist})

                    # here have to make sure we calculate to jump over any padding
                    ind += len(self._padding(field_length))

                else:
                    vlist = []
                    for _ in range(0, field_length):
                        vlist.append(ord(datar[ind]))
                        ind += 1
                    blk.update({"value": vlist})

                    # here have to make sure we calculate to jump over any padding
                    ind += len(self._padding(field_length))

                msgresp_dict["filter_blocks"].append(blk)

            # RESPONSE blocks
            msgresp_dict.update({"response_blocks": []})
            for _ in range(0, nresp_blocks):
                blk = {}
                blk.update({"framehdr": {}})
                blk["framehdr"].update({"src": ord(datar[ind])})
                ind += 1
                blk["framehdr"].update({"srcchan": ord(datar[ind])})
                ind += 1
                blk["framehdr"].update({"dst": ord(datar[ind])})
                ind += 1
                blk["framehdr"].update({"dstchan": ord(datar[ind])})
                ind += 1
                # skip the total datalen
                # totaldatalen = (ord(datar[ind]) * 256) + ord(datar[ind + 1])
                ind += 2
                frametype_raw = ord(datar[ind])
                # TODO create defines to replace constants
                frametype = ord(datar[ind]) & 0x3F
                flags = ord(datar[ind]) & 0xC0
                ind += 1
                blk["framehdr"].update({"frametype": frametype_raw})
                blk["framehdr"].update({"frametype_with_flags": frametype_raw})
                # TODO create defines to replace constants
                if flags & 0x80:
                    blk["framehdr"].update({"flag_dont_wait": True})
                else:
                    blk["framehdr"].update({"flag_dont_wait": False})
                if flags & 0x40:
                    blk["framehdr"].update({"flag_send_after": True})
                else:
                    blk["framehdr"].update({"flag_send_after": False})

                ind += 1  # reserved

                blk.update({"body": {}})
                blk["body"].update({"data": {}})

                if frametype == GryphonProtocolFT.FT_DATA:

                    hdrlen = ord(datar[ind])
                    blk["body"]["data"].update({"hdrlen": hdrlen})
                    ind += 1
                    blk["body"]["data"].update({"hdrbits": ord(datar[ind])})
                    ind += 1
                    datalen = (ord(datar[ind]) * 256) + ord(datar[ind + 1])
                    blk["body"]["data"].update({"datalen": datalen})
                    ind += 2
                    extralen = ord(datar[ind])
                    blk["body"]["data"].update({"extralen": extralen})
                    ind += 1
                    blk["body"]["data"].update({"mode": ord(datar[ind])})
                    ind += 1
                    blk["body"]["data"].update({"pri": ord(datar[ind])})
                    ind += 1
                    blk["body"]["data"].update({"status": ord(datar[ind])})
                    ind += 1
                    timestamp = (
                        (ord(datar[ind]) * 1024)
                        + (ord(datar[ind + 1]) * 512)
                        + (ord(datar[ind + 2]) * 256)
                        + ord(datar[ind + 3])
                    )
                    blk["body"]["data"].update({"status": timestamp})
                    ind += 4
                    blk["body"]["data"].update({"context": ord(datar[ind])})
                    ind += 1

                    ind += 3  # reserved

                    blk["body"]["data"].update({"hdr": []})
                    for _ in range(0, hdrlen):
                        blk["body"]["data"]["hdr"].append(ord(datar[ind]))
                        ind += 1
                    if datalen > 0:
                        blk["body"]["data"].update({"data": []})
                        for _ in range(0, datalen):
                            blk["body"]["data"]["data"].append(ord(datar[ind]))
                            ind += 1
                    if extralen > 0:
                        blk["body"]["data"].update({"extra": []})
                        for _ in range(0, extralen):
                            blk["body"]["data"]["extra"].append(ord(datar[ind]))
                            ind += 1

                    # here have to make sure we calculate to jump over any padding
                    ind += len(self._padding(hdrlen + datalen + extralen))

                elif frametype == GryphonProtocolFT.FT_EVENT:
                    # TODO implement FT_EVENT for CMD_MSGRESP_ADD()
                    raise self.ValueNotValid(frametype_raw)
                elif frametype == GryphonProtocolFT.FT_MISC:
                    # TODO implement FT_MISC for CMD_MSGRESP_ADD()
                    raise self.ValueNotValid(frametype_raw)
                elif frametype == GryphonProtocolFT.FT_TEXT:
                    # TODO implement FT_TEXT for CMD_MSGRESP_ADD()
                    raise self.ValueNotValid(frametype_raw)
                elif frametype == GryphonProtocolFT.FT_SIG:
                    # TODO implement FT_SIG for CMD_MSGRESP_ADD()
                    raise self.ValueNotValid(frametype_raw)
                else:
                    raise self.ValueNotInFT(frametype_raw)

                msgresp_dict["response_blocks"].append(blk)
        else:
            if datar[8] & GryphonProtocolFilterFlags.FILTER_FLAG_ACTIVE:
                filter_flag = GryphonProtocolFilterFlags.FILTER_FLAG_ACTIVE
            else:
                filter_flag = GryphonProtocolFilterFlags.FILTER_FLAG_INACTIVE
            msgresp_dict.update({"filter_flag": filter_flag})

            nfilter_blocks = datar[9]
            nresp_blocks = datar[10]

            old_handle = datar[11]
            msgresp_dict.update({"old_handle": old_handle})

            # action
            action = datar[12]  # raw action byte
            msgresp_dict.update({"action": action})  # raw action byte
            # action_code
            action_code = datar[12] & (
                GryphonProtocolMSGRESPActions.FR_RESP_AFTER_EVENT
                | GryphonProtocolMSGRESPActions.FR_RESP_AFTER_PERIOD
                | GryphonProtocolMSGRESPActions.FR_IGNORE_DURING_PER
            )
            msgresp_dict.update({"action_code": action_code})
            # action_flag
            action_flag = datar[12] & (
                GryphonProtocolMSGRESPActions.FR_PERIOD_MSGS
                | GryphonProtocolMSGRESPActions.FR_DELETE
                | GryphonProtocolMSGRESPActions.FR_DEACT_ON_EVENT
                | GryphonProtocolMSGRESPActions.FR_DEACT_AFTER_PER
            )
            msgresp_dict.update({"action_flag": action_flag})

            # TODO
            # if ord(datar[12]) & (GryphonProtocolMSGRESPActions.FR_DELETE):
            # if ord(datar[12]) & (GryphonProtocolMSGRESPActions.FR_DEACT_ON_EVENT):
            # if ord(datar[12]) & (GryphonProtocolMSGRESPActions.FR_DEACT_AFTER_PER):

            # reserverd datar[13]

            # action_value, action_time_value, action_message_counter_value
            action_value = (datar[14] * 256) + datar[15]
            msgresp_dict.update({"action_value": action_value})
            if datar[12] & GryphonProtocolMSGRESPActions.FR_PERIOD_MSGS:
                msgresp_dict.update({"action_message_counter_value": action_value})
            else:
                msgresp_dict.update({"action_time_value": action_value})

            # FILTER blocks
            msgresp_dict.update({"filter_blocks": []})
            ind = 16
            for _ in range(0, nfilter_blocks):
                blk = {}
                byte_offset = (datar[ind]) * 256 + datar[ind + 1]
                blk.update({"byte_offset": byte_offset})
                ind += 2

                field_length = (datar[ind] * 256) + datar[ind + 1]
                ind += 2

                data_type = datar[ind]
                blk.update({"data_type": data_type})
                ind += 1

                operator = datar[ind]
                blk.update({"operator": operator})
                ind += 1

                # reserved
                ind += 2

                if operator == GryphonProtocolFilterCondition.BIT_FIELD_CHECK:
                    plist = []
                    for _ in range(0, field_length):
                        plist.append(datar[ind])
                        ind += 1
                    blk.update({"pattern": plist})
                    mlist = []
                    for _ in range(0, field_length):
                        mlist.append(datar[ind])
                        ind += 1
                    blk.update({"mask": mlist})

                    # here have to make sure we calculate to jump over any padding
                    ind += len(self._padding(field_length * 2))

                elif operator in (
                    GryphonProtocolFilterCondition.DIG_LOW_TO_HIGH,
                    GryphonProtocolFilterCondition.DIG_HIGH_TO_LOW,
                    GryphonProtocolFilterCondition.DIG_TRANSITION,
                ):
                    bmlist = []
                    for _ in range(0, field_length):
                        bmlist.append(datar[ind])
                        ind += 1
                    blk.update({"bit_mask": bmlist})

                    # here have to make sure we calculate to jump over any padding
                    ind += len(self._padding(field_length))

                else:
                    vlist = []
                    for _ in range(0, field_length):
                        vlist.append(datar[ind])
                        ind += 1
                    blk.update({"value": vlist})

                    # here have to make sure we calculate to jump over any padding
                    ind += len(self._padding(field_length))

                msgresp_dict["filter_blocks"].append(blk)

            # RESPONSE blocks
            msgresp_dict.update({"response_blocks": []})
            for _ in range(0, nresp_blocks):
                blk = {}
                blk.update({"framehdr": {}})
                blk["framehdr"].update({"src": datar[ind]})
                ind += 1
                blk["framehdr"].update({"srcchan": datar[ind]})
                ind += 1
                blk["framehdr"].update({"dst": datar[ind]})
                ind += 1
                blk["framehdr"].update({"dstchan": datar[ind]})
                ind += 1
                # skip the total datalen
                # totaldatalen = (ord(datar[ind]) * 256) + ord(datar[ind + 1])
                ind += 2
                frametype_raw = datar[ind]
                # TODO create defines to replace constants
                frametype = datar[ind] & 0x3F
                flags = datar[ind] & 0xC0
                ind += 1
                blk["framehdr"].update({"frametype": frametype_raw})
                blk["framehdr"].update({"frametype_with_flags": frametype_raw})
                # TODO create defines to replace constants
                if flags & 0x80:
                    blk["framehdr"].update({"flag_dont_wait": True})
                else:
                    blk["framehdr"].update({"flag_dont_wait": False})
                if flags & 0x40:
                    blk["framehdr"].update({"flag_send_after": True})
                else:
                    blk["framehdr"].update({"flag_send_after": False})

                ind += 1  # reserved

                blk.update({"body": {}})
                blk["body"].update({"data": {}})

                if frametype == GryphonProtocolFT.FT_DATA:

                    hdrlen = datar[ind]
                    blk["body"]["data"].update({"hdrlen": hdrlen})
                    ind += 1
                    blk["body"]["data"].update({"hdrbits": datar[ind]})
                    ind += 1
                    datalen = (datar[ind] * 256) + datar[ind + 1]
                    blk["body"]["data"].update({"datalen": datalen})
                    ind += 2
                    extralen = datar[ind]
                    blk["body"]["data"].update({"extralen": extralen})
                    ind += 1
                    blk["body"]["data"].update({"mode": datar[ind]})
                    ind += 1
                    blk["body"]["data"].update({"pri": datar[ind]})
                    ind += 1
                    blk["body"]["data"].update({"status": datar[ind]})
                    ind += 1
                    timestamp = (
                        (datar[ind] * 1024)
                        + (datar[ind + 1] * 512)
                        + (datar[ind + 2] * 256)
                        + datar[ind + 3]
                    )
                    blk["body"]["data"].update({"status": timestamp})
                    ind += 4
                    blk["body"]["data"].update({"context": datar[ind]})
                    ind += 1

                    ind += 3  # reserved

                    blk["body"]["data"].update({"hdr": []})
                    for _ in range(0, hdrlen):
                        blk["body"]["data"]["hdr"].append(datar[ind])
                        ind += 1
                    if datalen > 0:
                        blk["body"]["data"].update({"data": []})
                        for _ in range(0, datalen):
                            blk["body"]["data"]["data"].append(datar[ind])
                            ind += 1
                    if extralen > 0:
                        blk["body"]["data"].update({"extra": []})
                        for _ in range(0, extralen):
                            blk["body"]["data"]["extra"].append(datar[ind])
                            ind += 1

                    # here have to make sure we calculate to jump over any padding
                    ind += len(self._padding(hdrlen + datalen + extralen))

                elif frametype == GryphonProtocolFT.FT_EVENT:
                    # TODO implement FT_EVENT for CMD_MSGRESP_ADD()
                    raise self.ValueNotValid(frametype_raw)
                elif frametype == GryphonProtocolFT.FT_MISC:
                    # TODO implement FT_MISC for CMD_MSGRESP_ADD()
                    raise self.ValueNotValid(frametype_raw)
                elif frametype == GryphonProtocolFT.FT_TEXT:
                    # TODO implement FT_TEXT for CMD_MSGRESP_ADD()
                    raise self.ValueNotValid(frametype_raw)
                elif frametype == GryphonProtocolFT.FT_SIG:
                    # TODO implement FT_SIG for CMD_MSGRESP_ADD()
                    raise self.ValueNotValid(frametype_raw)
                else:
                    raise self.ValueNotInFT(frametype_raw)

                msgresp_dict["response_blocks"].append(blk)
        reply_dict["GCprotocol"]["body"]["data"].update(msgresp_dict)
        return reply_dict

    def GGETBITRATE_IOCTL(self, chan):
        """IOCTL_GGETBITRATE = 0x11100018  # 4
        Args:
            chan, 1 <= chan <= n_channels
        Returns:
            dict
        Raises:
            self.ChannelNotValid(chan)

        """
        if chan == 0:
            raise self.ChannelNotValid(chan)

        databa = bytearray()
        ioctlbytes = struct.unpack(
            "4B", struct.pack(">I", GryphonProtocolIOCTL.IOCTL_GGETBITRATE)
        )
        databa.extend(ioctlbytes)
        databa.extend([0] * 4)
        reply_dict = self._build_and_send_command(
            dst=self.SD_CARD, dstchan=chan, cmd=self.BCMD_CARD_IOCTL, data=databa
        )
        reply_dict["GCprotocol"]["body"].update({"data": {}})
        datar = reply_dict["GCprotocol"]["body"][self.RAWDATA]
        ind = 8
        if sys.version_info[0] < 3:
            rate = (
                (ord(datar[ind + 3]) * 0x01000000)
                + (ord(datar[ind + 2]) * 0x010000)
                + (ord(datar[ind + 1]) * 0x0100)
                + ord(datar[ind])
            )
        else:
            rate = (
                (datar[ind + 3] * 0x01000000)
                + (datar[ind + 2] * 0x010000)
                + (datar[ind + 1] * 0x0100)
                + datar[ind]
            )
        reply_dict["GCprotocol"]["body"]["data"].update({"bitrate": rate})
        return reply_dict

    def GCANGETMODE_IOCTL(self, chan):
        """ IOCTL_GCANGETMODE = 0x11200005  # 1
        Args:
            chan, 1 <= chan <= n_channels
        Returns:
            dict
                MODE_CAN 0
                MODE_CANFD 1
                MODE_CANFD_PREISO 2
        Raises:
            self.ChannelNotValid(chan)

        """
        if chan == 0:
            raise self.ChannelNotValid(chan)

        databa = bytearray()
        ioctlbytes = struct.unpack(
            "4B", struct.pack(">I", GryphonProtocolIOCTL.IOCTL_GCANGETMODE)
        )
        databa.extend(ioctlbytes)
        databa.extend([0] * 1)
        reply_dict = self._build_and_send_command(
            dst=self.SD_CARD, dstchan=chan, cmd=self.BCMD_CARD_IOCTL, data=databa
        )
        reply_dict["GCprotocol"]["body"].update({"data": {}})
        datar = reply_dict["GCprotocol"]["body"][self.RAWDATA]
        ind = 8
        if sys.version_info[0] < 3:
            mode = ord(datar[ind])
        else:
            mode = datar[ind]
        reply_dict["GCprotocol"]["body"]["data"].update({"mode": mode})
        if mode == 0:
            reply_dict["GCprotocol"]["body"]["data"].update(
                {"mode_description": "MODE_CAN"}
            )
        elif mode == 1:
            reply_dict["GCprotocol"]["body"]["data"].update(
                {"mode_description": "MODE_CANFD"}
            )
        elif mode == 2:
            reply_dict["GCprotocol"]["body"]["data"].update(
                {"mode_description": "MODE_CANFD_PREISO"}
            )
        else:
            reply_dict["GCprotocol"]["body"]["data"].update(
                {"mode_description": "error unknown"}
            )
        return reply_dict

    def GCANSETMODE_IOCTL(self, chan, mode):
        """ IOCTL_GCANSETMODE = 0x11200006  # 1
        Args:
            chan, 1 <= chan <= n_channels
            mode, one of self.GryphonProtocolCANMode
                MODE_CAN 0
                MODE_CANFD 1
                MODE_CANFD_PREISO 2
        Returns:
            dict
        Raises:
            self.ChannelNotValid(chan)
            self.ValueNotValid(mode)

        """
        raise self.NotYetImplemented

    def FT_DATA_TX(self, chan, data_dict_in, wait_for_loopback=False):
        #
        # ----------------------------------------------------------------------
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        # TODO unused variable here
        # pylint: disable=unused-argument
        # ----------------------------------------------------------------------
        #
        """FT_DATA_TX

        Args:
            chan, 1 <= chan <= n_channels
            data_dict_in["hdr"][]  # can be one byte or a list of bytes or bytearray
            data_dict_in["data"][] (optional)  # can be one byte or a list of bytes or bytearray
            data_dict_in["extra"][] (optional)  # can be one byte or a list of bytes or bytearray
            data_dict_in["hdrlen"] (optional)  # must be hdrlen >= 1. If hdr is int, then must have hdrlen
            data_dict_in["hdrbits"] (optional)
            data_dict_in["datalen"][0,0] (optional)  # can be one byte or a list of bytes or bytearray
            data_dict_in["extralen"] (optional)
            data_dict_in["mode"] (optional)
            data_dict_in["pri"] (optional)
            data_dict_in["status"] (optional)
            data_dict_in["timestamp"] (optional)  # can be long, or a list of bytes or bytearray
            data_dict_in["context"] (optional)

        Pre:
            CMD_SERVER_REG()

        Post:

        Returns:

        Raises:
            None.
        """
        # TODO implement wait for TX loopback
        # done 20190103
        if chan == 0:
            raise self.ChannelNotValid(chan)

        if "hdr" not in data_dict_in:
            raise self.HdrNotFound()

        # hdrlen
        # %%%WARNING: must compute hdrlen before doing hdr[]
        hdrlen = None
        if "hdrlen" in data_dict_in:
            if isinstance(data_dict_in["hdrlen"], six.integer_types):
                hdrlen = data_dict_in["hdrlen"]
            else:
                # TODO
                raise self.ValueOutOfRange(data_dict_in["hdrlen"])

        # hdr
        hdr = []
        if isinstance(data_dict_in["hdr"], (list, bytearray)):
            if hdrlen is not None:
                # only use hdrlen number of elems from hdr[]
                maxhdr = min(hdrlen, len(data_dict_in["hdr"]))
                for ind in range(0, maxhdr):
                    hdr.append(data_dict_in["hdr"][ind])
            else:
                hdrlen = len(data_dict_in["hdr"])
                hdr = data_dict_in["hdr"]
        elif isinstance(data_dict_in["hdr"], int):
            if hdrlen is None:
                raise self.HdrLenNotFound()
            # split hdr into hdrlen number of bytes
            for ind in range(0, hdrlen):
                mask = 0x00FF << (8 * ind)
                num = data_dict_in["hdr"] * mask
                mybyte = num >> (8 * ind)
                hdr.append(mybyte)
            # reverse the list
            hdr.reverse()
        else:
            raise self.HdrNotFound(data_dict_in["hdr"])

        # hdrbits
        hdrbits = 11  # CANbus 11-bit header, default
        if "hdrbits" in data_dict_in:
            hdrbits = data_dict_in["hdrbits"]
        else:
            if hdrlen == 1:  # LINbus header
                hdrbits = 8
            elif hdrlen == 4:  # CANbus 29-bit header
                hdrbits = 29
            else:
                hdrbits = 11  # CANbus 11-bit header

        # datalen
        # %%%WARNING: must compute datalen before doing data[]
        datalen = None
        if "datalen" in data_dict_in:
            if isinstance(data_dict_in["datalen"], six.integer_types):
                datalen = data_dict_in["datalen"]
            else:
                raise self.ValueOutOfRange(data_dict_in["datalen"])
        else:
            if "data" in data_dict_in:
                datalen = len(data_dict_in["data"])
            else:
                datalen = 0
        # convert into two bytes
        datalen1 = (datalen & 0xFF00) >> 8
        datalen2 = (datalen & 0x00FF) >> 0

        # data
        data = None
        if "data" in data_dict_in:
            if isinstance(data_dict_in["data"], (list, bytearray)):
                data = []
                maxdata = min(datalen, len(data_dict_in["data"]))
                for ind in range(0, maxdata):
                    data.append(data_dict_in["data"][ind])
            else:
                # is single int
                data = []
                data.append(data_dict_in["data"])

        # extralen
        # %%%WARNING: must compute extralen before doing extra[]
        if "extralen" in data_dict_in:
            if isinstance(data_dict_in["extralen"], six.integer_types):
                extralen = data_dict_in["extralen"]
            else:
                # TODO
                raise self.ExtraLenNotFound()
        else:
            if "extra" in data_dict_in:
                extralen = len(data_dict_in["extra"])
            else:
                extralen = 0

        # extra
        extra = None
        if "extra" in data_dict_in:
            if isinstance(data_dict_in["extra"], (list, bytearray)):
                extra = []
                maxextra = min(extralen, len(data_dict_in["extra"]))
                for ind in range(0, maxextra):
                    extra.append(data_dict_in["extra"][ind])
            else:
                # is single int
                extra = []
                extra.append(data_dict_in["extra"])

        if "mode" in data_dict_in:
            mode = data_dict_in["mode"]
        else:
            # mode = GryphonProtocolRxTxMode.MODE_TX
            mode = 0  # transmit message, no special mode

        if "pri" in data_dict_in:
            pri = data_dict_in["pri"]
        else:
            pri = 0

        if "status" in data_dict_in:
            status = data_dict_in["status"]
        else:
            status = 0

        timestamp = []
        if "timestamp" in data_dict_in:
            if isinstance(data_dict_in["timestamp"], list):
                timestamp = data_dict_in["timestamp"]
            else:
                # turn int into a list
                # TODO
                timestamp.append(
                    ((data_dict_in["timestamp"] & 0xFF000000) >> 24) & 0xFF
                )
                timestamp.append(
                    ((data_dict_in["timestamp"] & 0x00FF0000) >> 16) & 0xFF
                )
                timestamp.append(((data_dict_in["timestamp"] & 0x0000FF00) >> 8) & 0xFF)
                timestamp.append(((data_dict_in["timestamp"] & 0x000000FF) >> 0) & 0xFF)
        else:
            timestamp = [0, 0, 0, 0]

        if "context" in data_dict_in:
            context = data_dict_in["context"]
        else:
            context = self.cmd_context

        gcframe = bytearray()
        gcframe.extend(
            [hdrlen, hdrbits, datalen1, datalen2]
        )  # BEACON data header, hdrlen, hdrbits, data len
        gcframe.extend(
            [extralen, mode, pri, status]
        )  # BEACON data header, extralen, mode, pri, status
        gcframe.extend(timestamp)  # BEACON data header, timestamp
        gcframe.extend([context, 0, 0, 0])  # BEACON data header, context, resv
        gcframe.extend(hdr)  # msg header
        if data is not None:
            gcframe.extend(data)  # msg data
        if extra is not None:
            gcframe.extend(extra)  # msg extra
        self._build_and_send_data(dst=self.SD_CARD, dstchan=chan, data=gcframe)
        reply_dict = {"response_return_code": GryphonProtocolResp.RESP_OK}
        return reply_dict

    def FT_MISC_TX(self, src_in, srcchan_in, dst_in, dstchan_in, data_in):
        #
        # ----------------------------------------------------------------------
        # pylint: disable=too-many-arguments
        # ----------------------------------------------------------------------
        #
        """send an FT_MISC frame
        Not Yet Implemented

        Args:
            chan, 1 <= chan <= n_channels
            msg

        Pre:
            CMD_SERVER_REG()

        Post:

        Returns:

        Raises:
            None.
        """
        raise self.NotYetImplemented

    def FT_DATA_WAIT_FOR_RX(self, hdr=None, data=None, timeout=0.05):
        """FT_DATA_WAIT_FOR_RX, wait to read a rx msg

        Args:
            hdr - not used yet
            data - not used yet
            timeout - max time to wait for a rx

        Pre:
            CMD_SERVER_REG()

        Post:

        Returns:
            None on timeout

        Raises:
            None.
        """
        # done 20190103
        # TODO implement wait for hdr and data
        # print("=DEBUG=======================timeout {}".format(timeout))
        reply = self._wait_and_read_rx(
            frametype=GryphonProtocolFT.FT_DATA, hdr=hdr, data=data, timeout=timeout
        )
        if reply is None:
            return reply

        # Now construct the reply, just opposite of the tx
        datar = reply["GCprotocol"]["body"][self.RAWDATA]
        reply["GCprotocol"]["body"].update({"data": {}})
        if sys.version_info[0] < 3:
            hdrlen = ord(datar[0])
            reply["GCprotocol"]["body"]["data"].update({"hdrlen": hdrlen})
            reply["GCprotocol"]["body"]["data"].update({"hdrbits": ord(datar[1])})
            datalen = (ord(datar[2]) * 256) + ord(datar[3])
            reply["GCprotocol"]["body"]["data"].update({"datalen": datalen})
            extralen = ord(datar[4])
            reply["GCprotocol"]["body"]["data"].update({"extralen": extralen})
            reply["GCprotocol"]["body"]["data"].update({"mode": ord(datar[5])})
            reply["GCprotocol"]["body"]["data"].update({"pri": ord(datar[6])})
            reply["GCprotocol"]["body"]["data"].update({"status": ord(datar[7])})
            timestamp = 0
            timestamp += ord(datar[8]) << 24
            timestamp += ord(datar[9]) << 16
            timestamp += ord(datar[10]) << 8
            timestamp += ord(datar[11]) << 0
            rollover = 0xFFFFFFFF  # max in 10's of microseconds
            rollover -= timestamp
            timestamp *= 10
            rollover *= 10
            rollover = int(rollover / 1000000)
            reply["GCprotocol"]["body"]["data"].update({"timestamp": timestamp})
            reply["GCprotocol"]["body"]["data"].update(
                {"seconds to rollover": rollover}
            )
            reply["GCprotocol"]["body"]["data"].update({"context": ord(datar[12])})
            reply["GCprotocol"]["body"]["data"].update({"hdr": []})
            ind = 16
            for item in datar[ind : ind + hdrlen]:
                reply["GCprotocol"]["body"]["data"]["hdr"].append(ord(item))
            ind = ind + hdrlen
            if datalen > 0:
                reply["GCprotocol"]["body"]["data"].update({"data": []})
                for item in datar[ind : ind + datalen]:
                    reply["GCprotocol"]["body"]["data"]["data"].append(ord(item))
                ind = ind + datalen
            if extralen > 0:
                reply["GCprotocol"]["body"]["data"].update({"extra": []})
                for item in datar[ind : ind + extralen]:
                    reply["GCprotocol"]["body"]["data"]["extra"].append(ord(item))
        else:
            hdrlen = datar[0]
            reply["GCprotocol"]["body"]["data"].update({"hdrlen": hdrlen})
            reply["GCprotocol"]["body"]["data"].update({"hdrbits": datar[1]})
            datalen = (datar[2] * 256) + datar[3]
            reply["GCprotocol"]["body"]["data"].update({"datalen": datalen})
            extralen = datar[4]
            reply["GCprotocol"]["body"]["data"].update({"extralen": extralen})
            reply["GCprotocol"]["body"]["data"].update({"mode": datar[5]})
            reply["GCprotocol"]["body"]["data"].update({"pri": datar[6]})
            reply["GCprotocol"]["body"]["data"].update({"status": datar[7]})
            timestamp = 0
            timestamp += datar[8] << 24
            timestamp += datar[9] << 16
            timestamp += datar[10] << 8
            timestamp += datar[11] << 0
            rollover = 0xFFFFFFFF  # max in 10's of microseconds
            rollover -= timestamp
            timestamp *= 10
            rollover *= 10
            rollover = int(rollover / 1000000)
            reply["GCprotocol"]["body"]["data"].update({"timestamp": timestamp})
            reply["GCprotocol"]["body"]["data"].update(
                {"seconds to rollover": rollover}
            )
            reply["GCprotocol"]["body"]["data"].update({"context": datar[12]})
            reply["GCprotocol"]["body"]["data"].update({"hdr": []})
            ind = 16
            for item in datar[ind : ind + hdrlen]:
                reply["GCprotocol"]["body"]["data"]["hdr"].append(item)
            ind = ind + hdrlen
            if datalen > 0:
                reply["GCprotocol"]["body"]["data"].update({"data": []})
                for item in datar[ind : ind + datalen]:
                    reply["GCprotocol"]["body"]["data"]["data"].append(item)
                ind = ind + datalen
            if extralen > 0:
                reply["GCprotocol"]["body"]["data"].update({"extra": []})
                for item in datar[ind : ind + extralen]:
                    reply["GCprotocol"]["body"]["data"]["extra"].append(item)

        return reply

    def FT_TEXT_WAIT_FOR_RX(self, timeout=0.25):
        """FT_TEXT_WAIT_FOR_RX, wait to read a text frame such as a broadcast frame

        Args:
            timeout - max time to wait for a rx

        Pre:
            CMD_SERVER_REG()
            CMD_BCAST_ON() to receive broadcast messages

        Post:

        Returns:
            None on timeout

        Raises:
            None.
        """
        # 20190605
        # 20190626 TODO

        reply_dict = self._wait_and_read_rx(
            frametype=GryphonProtocolFT.FT_TEXT, timeout=timeout
        )
        if reply_dict is None:
            return reply_dict

        # datar = reply_dict["GCprotocol"]["body"][self.RAWDATA]
        msg = "".join(reply_dict["GCprotocol"]["body"]["rawdata"])
        reply_dict["GCprotocol"]["body"].update({"text": msg})
        return reply_dict

    def FT_SIG_WAIT_FOR_RX(self, hdr=None, data=None, timeout=0.25):
        """FT_SIG_WAIT_FOR_RX, wait to read a rx signal frame

        Args:
            hdr - not used yet
            data - not used yet
            timeout - max time to wait for a rx

        Pre:
            CMD_SERVER_REG()
            CMD_READ_CNVT_CONFIG(filename)
            CMD_CNVT_GET_MSG_NAMES()
            CMD_CNVT_GET_SIG_NAMES()
            CMD_CNVT_REQ_VALUES()
            config file filename is already upload to BEACON using the BEACON web page

        Post:

        Returns:
            None on timeout

        Raises:
            None.
        """
        # done 20190311
        # TODO implement wait for hdr and data
        reply_dict = self._wait_and_read_rx(
            frametype=GryphonProtocolFT.FT_SIG, hdr=hdr, data=data, timeout=timeout
        )
        if reply_dict is None:
            return reply_dict
        datar = reply_dict["GCprotocol"]["body"][self.RAWDATA]
        reply_dict["GCprotocol"]["body"].update({"data": {}})
        idx = 0
        timestamp = 0
        if sys.version_info[0] < 3:
            timestamp += ord(datar[idx + 0]) << 24
            timestamp += ord(datar[idx + 1]) << 16
            timestamp += ord(datar[idx + 2]) << 8
            timestamp += ord(datar[idx + 3]) << 0
            reply_dict["GCprotocol"]["body"]["data"].update({"timestamp": timestamp})
            idx += 4
            mode = ord(datar[idx])
            reply_dict["GCprotocol"]["body"]["data"].update({"mode": mode})
            idx += 1
            request_index = ord(datar[idx])
            reply_dict["GCprotocol"]["body"]["data"].update(
                {"request_index": request_index}
            )
            idx += 1
            number_of_signals = ord(datar[idx])
            reply_dict["GCprotocol"]["body"]["data"].update(
                {"number_of_signals": number_of_signals}
            )
            idx += 1
            idx += 1
            reply_dict["GCprotocol"]["body"]["data"].update({"signals": []})
            for _ in range(0, number_of_signals):
                mysignal = {}
                flags = ord(datar[idx])
                mysignal.update({"flags": flags})
                idx += 1
                if flags & 0x01:
                    mysignal.update({"flag_fp": True})
                if flags & 0x02:
                    mysignal.update({"flag_int": True})
                if flags & 0x04:
                    mysignal.update({"flag_str": True})
                if flags & 0x08:
                    mysignal.update({"flag_under_range": True})
                if flags & 0x10:
                    mysignal.update({"flag_over_range": True})
                index = ord(datar[idx])
                mysignal.update({"index": index})
                idx += 1
                # Yes, FT_SIG may contain an int and a string!
                if flags & 0x01:
                    # do fp
                    fpba = bytearray()
                    fpba.extend([ord(datar[idx + 3])])
                    fpba.extend([ord(datar[idx + 2])])
                    fpba.extend([ord(datar[idx + 1])])
                    fpba.extend([ord(datar[idx + 0])])
                    fp = struct.unpack("f", fpba)[0]
                    mysignal.update({"value_fp": fp})
                    idx += 4
                if flags & 0x02:
                    # do int
                    value = 0
                    value += ord(datar[idx + 0]) << 24
                    value += ord(datar[idx + 1]) << 16
                    value += ord(datar[idx + 2]) << 8
                    value += ord(datar[idx + 3]) << 0
                    mysignal.update({"value_int": value})
                    idx += 4
                if flags & 0x04:
                    # do string
                    end = idx + datar[idx:].index(
                        "\x00"
                    )  # find first null at end of C string
                    value = "".join(datar[idx:end])
                    mysignal.update({"value_string": value})
                    idx = end

                reply_dict["GCprotocol"]["body"]["data"]["signals"].append(mysignal)
        else:
            timestamp += datar[idx + 0] << 24
            timestamp += datar[idx + 1] << 16
            timestamp += datar[idx + 2] << 8
            timestamp += datar[idx + 3] << 0
            reply_dict["GCprotocol"]["body"]["data"].update({"timestamp": timestamp})
            idx += 4
            mode = datar[idx]
            reply_dict["GCprotocol"]["body"]["data"].update({"mode": mode})
            idx += 1
            request_index = datar[idx]
            reply_dict["GCprotocol"]["body"]["data"].update(
                {"request_index": request_index}
            )
            idx += 1
            number_of_signals = datar[idx]
            reply_dict["GCprotocol"]["body"]["data"].update(
                {"number_of_signals": number_of_signals}
            )
            idx += 1
            idx += 1
            reply_dict["GCprotocol"]["body"]["data"].update({"signals": []})
            for _ in range(0, number_of_signals):
                mysignal = {}
                flags = datar[idx]
                mysignal.update({"flags": flags})
                idx += 1
                if flags & 0x01:
                    mysignal.update({"flag_fp": True})
                if flags & 0x02:
                    mysignal.update({"flag_int": True})
                if flags & 0x04:
                    mysignal.update({"flag_str": True})
                if flags & 0x08:
                    mysignal.update({"flag_under_range": True})
                if flags & 0x10:
                    mysignal.update({"flag_over_range": True})
                index = datar[idx]
                mysignal.update({"index": index})
                idx += 1
                # Yes, FT_SIG may contain an int and a string!
                if flags & 0x01:
                    # do fp
                    fpba = bytearray()
                    fpba.extend([datar[idx + 3]])
                    fpba.extend([datar[idx + 2]])
                    fpba.extend([datar[idx + 1]])
                    fpba.extend([datar[idx + 0]])
                    fp = struct.unpack("f", fpba)[0]
                    mysignal.update({"value_fp": fp})
                    idx += 4
                if flags & 0x02:
                    # do int
                    value = 0
                    value += datar[idx + 0] << 24
                    value += datar[idx + 1] << 16
                    value += datar[idx + 2] << 8
                    value += datar[idx + 3] << 0
                    mysignal.update({"value_int": value})
                    idx += 4
                if flags & 0x04:
                    # do string
                    end = idx + datar[idx:].index(
                        0
                    )  # find first null at end of C string
                    value = "".join(map(chr, datar[idx:end]))
                    mysignal.update({"value_string": value})
                    idx = end

        return reply_dict

    def WAIT_FOR_EVENT(self, chan, event=None):
        """wait for an event
        Not Yet Implemented

        Args:
            chan, 1 <= chan <= n_channels

        Pre:
            CMD_SERVER_REG()

        Post:

        Returns:

        Raises:
            None.
        """
        # return self._wait_and_read_event(srcchan=chan, event=event)
        raise self.NotYetImplemented

    def get_client_id(self):
        """get client_id

        Args:
            none.

        Pre:
            CMD_SERVER_REG()

        Post:

        Returns:
            client_id, or None

        Raises:
            None.
        """
        return self.client_id


#
# ----------------------------------------------------------------------
# pylint: disable=too-many-ancestors
# ----------------------------------------------------------------------
#
class BEACON(Gryphon):
    """BEACON
      aliased to Gryphon class
    """


#
# ----------------------------------------------------------------------
# pylint: enable=too-many-ancestors
# ----------------------------------------------------------------------
#


def signal_handler(signal_in, frame_in):
    """handle Ctrl-C

    Args:
        signal -
        frame -

    Returns:
        none.

    Raises:
        none.
    """
    #
    # ----------------------------------------------------------------------
    # unused-argument
    # variable is ok here
    # ----------------------------------------------------------------------
    _, _ = signal_in, frame_in
    _ = _
    #
    # --------------------------------------------------------------------------
    # pylint: disable=global-statement
    # pylint: disable=global-variable-not-assigned
    # --------------------------------------------------------------------------
    #
    global GRYPHON_THREADED_CLIENT
    if GRYPHON_THREADED_CLIENT:
        GRYPHON_THREADED_CLIENT.kill()
        GRYPHON_THREADED_CLIENT = None


def main():
    """main
      This is just an example, normally this file is used as a module, and this main is not used
    """

    # install ctrl-C signal_handler
    signal.signal(signal.SIGINT, signal_handler)

    ip_address = "10.94.44.185"
    try:
        beacon = BEACON(ip_address)
        gryph = Gryphon(ip_address)
        gryph2 = Gryphon(ip_address)
    except socket.timeout:
        six.print_("socket.timeout: cannot connect to {}".format(ip_address))
        return
    client_id = gryph.CMD_SERVER_REG()
    six.print_("successfully registered as client id {}".format(client_id))
    client_id2 = gryph2.CMD_SERVER_REG()
    six.print_("successfully registered as client id {}".format(client_id2))
    configarray = gryph.CMD_GET_CONFIG()
    if configarray is not None:
        six.print_("device_name: {}".format(configarray["device_name"]))
    beacon_id = beacon.CMD_SERVER_REG()
    six.print_("successfully registered as BEACON client id {}".format(beacon_id))


if __name__ == "__main__":
    # doctest.testmod()
    main()

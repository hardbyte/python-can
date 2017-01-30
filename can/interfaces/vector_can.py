"""
Vector can interface module.
Use VectorCan.pyd to access to the vector hardware, no need other dll or lib,
but only work on python3 32 bit.
you can get the VectorCan.pyd  file from:https://github.com/sgnes/BoostVXL.git
if you have any problem with this, sgnes0514@gmail.com.
"""
import logging
import sys
from ctypes import *
from can import CanError, BusABC, Message
import VectorCan
import time
if sys.version_info >= (3, 3):
    # new in 3.3
    timeout_clock = time.perf_counter
else:
    # deprecated in 3.3
    timeout_clock = time.clock
 

# driver status
XL_SUCCESS = 0
XL_PENDING = 1
XL_ERR_QUEUE_IS_EMPTY = 10
XL_ERR_QUEUE_IS_FULL = 11
XL_ERR_TX_NOT_POSSIBLE = 12
XL_ERR_NO_LICENSE = 14
XL_ERR_WRONG_PARAMETER = 101
XL_ERR_TWICE_REGISTER = 110
XL_ERR_INVALID_CHAN_INDEX = 111
XL_ERR_INVALID_ACCESS = 112
XL_ERR_PORT_IS_OFFLINE = 113
XL_ERR_CHAN_IS_ONLINE = 116
XL_ERR_NOT_IMPLEMENTED = 117
XL_ERR_INVALID_PORT = 118
XL_ERR_HW_NOT_READY = 120
XL_ERR_CMD_TIMEOUT = 121
XL_ERR_HW_NOT_PRESENT = 129
XL_ERR_NOTIFY_ALREADY_ACTIVE = 131
XL_ERR_NO_RESOURCES = 152
XL_ERR_WRONG_CHIP_TYPE = 153
XL_ERR_WRONG_COMMAND = 154
XL_ERR_INVALID_HANDLE = 155
XL_ERR_CANNOT_OPEN_DRIVER = 201
XL_ERR_WRONG_BUS_TYPE = 202
XL_ERROR = 255


XL_CAN_MSG_FLAG_NERR            =       0x04           #//!< Line Error on Lowspeed
XL_CAN_MSG_FLAG_WAKEUP          =       0x08          # //!< High Voltage Message on Single Wire CAN
XL_CAN_MSG_FLAG_REMOTE_FRAME    =       0x10
XL_CAN_MSG_FLAG_RESERVED_1      =       0x20
XL_CAN_MSG_FLAG_TX_COMPLETED    =       0x40           #//!< Message Transmitted
XL_CAN_MSG_FLAG_TX_REQUEST = 0x80 



class vectorcan(BusABC):
    def __init__(self, channel, **kwargs):
        """
        :param int channel_index:
            the index of the channel to open (e.g. '01')

        On top of the usual :class:`~can.Bus` methods provided,
        the PCAN interface includes the `flash()` and `status()` methods.

        :param str channel:
            The can interface name. An example would be PCAN_USBBUS1

        :param int bitrate:
            Bitrate of channel in bit/s.
            Default is 500 Kbs

        """
        if channel is None or channel == '':
            raise ArgumentError("Must specify a PCAN channel")
        else:
            self.channel_info = channel

        bitrate = kwargs.get('bitrate', 500000)


        self.m_objVectorCan = VectorCan.Can()

        self.m_objVectorCan.openChannels(int(channel), bitrate, 1)
        self.logger = logging.getLogger(__name__)
        self.__msg_list = []

    def _get_formatted_error(self, error):
        """
        Gets the text using the GetErrorText API function
        If the function succeeds, the translated error is returned. If it fails,
        a text describing the current error is returned.  Multiple errors may
        be present in which case their individual messages are included in the
        return string, one line per error.
        """

        def bits(n):
            while n:
                b = n & (~n+1)
                yield b
                n ^= b

        stsReturn = self.m_objPCANBasic.GetErrorText(error, 0)
        if stsReturn[0] != 0:
            strings = []

            for b in bits(error):
                stsReturn = self.m_objPCANBasic.GetErrorText(b, 0)
                if stsReturn[0] != 0:
                    text = "An error occurred. Error-code's text ({0:X}h) couldn't be retrieved".format(error)
                else:
                    text = stsReturn[1].decode('utf-8')

                strings.append(text)

            complete_text = '\n'.join(strings)
        else:
            complete_text = stsReturn[1].decode('utf-8')

        return complete_text


    def recv(self, timeout=None):
        start_time = timeout_clock()

        if timeout is None:
            timeout = 0

        self.logger.debug("Trying to read a msg")

        result = None
        while result is None:
            result = self.m_objVectorCan.read()
            if result is None:
                if timeout_clock() - start_time >= timeout:
                    return None
                else:
                    result = None
                    time.sleep(0.001)
        for i in result:
            self.__msg_list.append(i)
        msg = self.__msg_list.pop(0)

        self.logger.debug("Received a message")

        bIsRTR = (msg.flag & XL_CAN_MSG_FLAG_REMOTE_FRAME) == XL_CAN_MSG_FLAG_REMOTE_FRAME
        bIsExt = 0

        if bIsExt:
            #rx_msg.id_type = ID_TYPE_EXTENDED
            self.logger.debug("CAN: Extended")
        else:
            #rx_msg.id_type = ID_TYPE_STANDARD
            self.logger.debug("CAN: Standard")

        dlc = msg.dlc
        timestamp = msg.time

        rx_msg = Message(timestamp=timestamp,
                         arbitration_id=msg.id,
                         extended_id=bIsExt,
                         is_remote_frame=bIsRTR,
                         dlc=dlc,
                         data=msg.msg)

        return rx_msg

    def send(self, msg):

        if msg.is_remote_frame:
            flag = XL_CAN_MSG_FLAG_REMOTE_FRAME
        else:
            flag = 0

        # create a TPCANMsg message structure
        canmsg = VectorCan.CanMsg(msg.arbitration_id, list(msg.data), flag)

        # configure the message. ID, Length of data, message type and data
        

        self.logger.debug("Data: %s", msg.data)
        self.logger.debug("Type: %s", type(msg.data))

        result = self.m_objVectorCan.write([canmsg])
        if result != XL_SUCCESS:
            raise vectorcanError("Failed to send: " + self._get_formatted_error(result))


class vectorcanError(CanError):
    pass


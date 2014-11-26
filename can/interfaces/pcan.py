"""
Enable basic can over a PCAN USB device.

"""
import logging

logger = logging.getLogger(__name__)

from can.interfaces.PCANBasic import *
from can.bus import BusABC
from can.message import Message

boottimeEpoch = 0
try:
    import uptime
    import datetime
    boottimeEpoch = (uptime.boottime() - datetime.datetime.utcfromtimestamp(0)).total_seconds()
except:
    boottimeEpoch = 0

# Set up logging
logging.basicConfig(level=logging.WARNING)
log = logging.getLogger('can.pcan')


class Bus(BusABC):

    def __init__(self, channel, *args, **kwargs):
        """A PCAN USB interface to CAN.

        :param str channel:
            The can interface name.  An example would be PCAN_USBBUS1
        """
        if channel == '':
            raise TypeError("Must specify a PCAN channel.")
        else:
            self.channel_info = channel

        baudrate = PCAN_BAUD_500K
        hwtype = PCAN_TYPE_ISA
        ioport = 0x02A0
        interrupt = 11

        self.m_objPCANBasic = PCANBasic()
        self.m_PcanHandle = globals()[channel]

        result = self.m_objPCANBasic.Initialize(self.m_PcanHandle, baudrate, hwtype, ioport, interrupt)

        if result != PCAN_ERROR_OK:
            raise Exception(self.GetFormattedError(result))

        super(Bus, self).__init__(*args, **kwargs)

    def GetFormattedError(self, error):
        # Gets the text using the GetErrorText API function
        # If the function success, the translated error is returned. If it fails,
        # a text describing the current error is returned.
        #
        #return error
        stsReturn = self.m_objPCANBasic.GetErrorText(error, 0)
        if stsReturn[0] != PCAN_ERROR_OK:
            return "An error occurred. Error-code's text ({0:X}h) couldn't be retrieved".format(error)
        else:
            return stsReturn[1]

    def recv(self, timeout=None):
        rx_msg = Message()

        log.debug("Trying to read a msg")

        result = self.m_objPCANBasic.Read(self.m_PcanHandle)
        if result[0] == PCAN_ERROR_QRCVEMPTY or result[0] == PCAN_ERROR_BUSLIGHT or result[0] == PCAN_ERROR_BUSHEAVY:
            return None
        elif result[0] != PCAN_ERROR_OK:
            raise Exception(self.GetFormattedError(result[0]))

        theMsg = result[1]
        itsTimeStamp = result[2]

        log.debug("I've got a message")

        arbitration_id = theMsg.ID

        bIsRTR = (theMsg.MSGTYPE & PCAN_MESSAGE_RTR.value) == PCAN_MESSAGE_RTR.value
        bIsExt = (theMsg.MSGTYPE & PCAN_MESSAGE_EXTENDED.value) == PCAN_MESSAGE_EXTENDED.value

        # Flags: EXT, RTR, ERR
        #flags = (PYCAN_RTRFLG if bIsRTR else 0) | (PYCAN_STDFLG if not bIsExt else 0)

        if bIsExt:
            #rx_msg.id_type = ID_TYPE_EXTENDED
            log.debug("CAN: Extended")
        else:
            #rx_msg.id_type = ID_TYPE_STANDARD
            log.debug("CAN: Standard")

        rx_msg.arbitration_id = arbitration_id
        rx_msg.id_type = bIsExt
        rx_msg.is_remote_frame = bIsRTR
        rx_msg.dlc = theMsg.LEN
        #rx_msg.flags = flags
        rx_msg.data = theMsg.DATA
        rx_msg.timestamp = boottimeEpoch + ((itsTimeStamp.micros + (1000 * itsTimeStamp.millis)) / (1000.0 * 1000.0))

        return rx_msg

    def send(self, msg):
        if msg.id_type:
            msgType = PCAN_MESSAGE_EXTENDED
        else:
            msgType = PCAN_MESSAGE_STANDARD

        # create a TPCANMsg message structure
        CANMsg = TPCANMsg()

        # configure the message. ID, Length of data, message type and data
        CANMsg.ID = msg.arbitration_id
        CANMsg.LEN = len(msg.data)
        CANMsg.MSGTYPE = msgType

        # if a remote frame will be sent, data bytes are not important.
        if msg.is_remote_frame:
            CANMsg.MSGTYPE = msgType | PCAN_MESSAGE_RTR
        else:
            # copy data
            for i in range(CANMsg.LEN):
                CANMsg.DATA[i] = msg.data[i]

        log.debug("Data: {}".format(msg.data))
        log.debug("type: {}".format(type(msg.data)))

        result = self.m_objPCANBasic.Write(self.m_PcanHandle, CANMsg)

        if result != PCAN_ERROR_OK:
            logging.error("Error sending frame :-/ " + self.GetFormattedError(result))

"""
Enable basic can over a PCAN USB device.

"""
import logging
import sys

logger = logging.getLogger(__name__)

from can.interfaces.PCANBasic import *
from can.bus import BusABC
from can.message import Message
import time

boottimeEpoch = 0
try:
    import uptime
    import datetime
    boottimeEpoch = (uptime.boottime() - datetime.datetime.utcfromtimestamp(0)).total_seconds()
except:
    boottimeEpoch = 0

if sys.version_info >= (3, 3):
    # new in 3.3
    timeout_clock = time.perf_counter
else:
    # deprecated in 3.3
    timeout_clock = time.clock

# Set up logging
logging.basicConfig(level=logging.WARNING)
log = logging.getLogger('can.pcan')


pcan_bitrate_objs = {1000000 : PCAN_BAUD_1M,
                      800000 : PCAN_BAUD_800K,
                      500000 : PCAN_BAUD_500K,
                      250000 : PCAN_BAUD_250K,
                      125000 : PCAN_BAUD_125K,
                      100000 : PCAN_BAUD_100K,
                       95000 : PCAN_BAUD_95K,
                       83000 : PCAN_BAUD_83K,
                       50000 : PCAN_BAUD_50K,
                       47000 : PCAN_BAUD_47K,
                       33000 : PCAN_BAUD_33K,
                       20000 : PCAN_BAUD_20K,
                       10000 : PCAN_BAUD_10K,
                        5000 : PCAN_BAUD_5K}


class PcanBus(BusABC):

    def __init__(self, channel, *args, **kwargs):
        """A PCAN USB interface to CAN.

        On top of the usual :class:`~can.Bus` methods provided,
        the PCAN interface includes the `flash()` and `status()` methods.

        :param str channel:
            The can interface name. An example would be PCAN_USBBUS1
            
        Backend Configuration
        ---------------------
            
        :param int bitrate:
            Bitrate of channel in bit/s.
            Default is 500 Kbs
            
        """
        if channel is None or channel == '':
            raise ArgumentError("Must specify a PCAN channel")
        else:
            self.channel_info = channel

        bitrate = kwargs.get('bitrate', 500000)
        pcan_bitrate = pcan_bitrate_objs.get(bitrate, PCAN_BAUD_500K)
        
        hwtype = PCAN_TYPE_ISA
        ioport = 0x02A0
        interrupt = 11

        self.m_objPCANBasic = PCANBasic()
        self.m_PcanHandle = globals()[channel]

        result = self.m_objPCANBasic.Initialize(self.m_PcanHandle, pcan_bitrate, hwtype, ioport, interrupt)

        if result != PCAN_ERROR_OK:
            # TODO throw a specific exception.
            raise Exception(self._get_formatted_error(result))

        super(PcanBus, self).__init__(*args, **kwargs)

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
        if stsReturn[0] != PCAN_ERROR_OK:
            strings = []

            for b in bits(error):
                stsReturn = self.m_objPCANBasic.GetErrorText(b, 0)
                if stsReturn[0] != PCAN_ERROR_OK:
                    text = "An error occurred. Error-code's text ({0:X}h) couldn't be retrieved".format(error)
                else:
                    text = stsReturn[1].decode('utf-8')

                strings.append(text)

            complete_text = '\n'.join(strings)
        else:
            complete_text = stsReturn[1].decode('utf-8')

        return complete_text

    def status(self):
        """
        Query the PCAN bus status.

        :return: The status code. See values in pcan_constants.py
        """
        return self.m_objPCANBasic.GetStatus(self.channel_info)

    def status_is_ok(self):
        """
        Convenience method to check that the bus status is OK
        """
        status = self.status()
        return status == PCAN_ERROR_OK

    def reset(self):
        # Command the PCAN driver to reset the bus after an error.

        status = self.m_objPCANBasic.Reset(self.channel_info)

        return status == PCAN_ERROR_OK

    def recv(self, timeout=None):
        start_time = timeout_clock()

        if timeout is None:
            timeout = 0

        rx_msg = Message()

        log.debug("Trying to read a msg")

        result = None
        while result is None:
            result = self.m_objPCANBasic.Read(self.m_PcanHandle)
            if result[0] == PCAN_ERROR_QRCVEMPTY or result[0] == PCAN_ERROR_BUSLIGHT or result[0] == PCAN_ERROR_BUSHEAVY:
                if timeout_clock() - start_time >= timeout:
                    return None
                else:
                    result = None
                    time.sleep(0.001)
            elif result[0] != PCAN_ERROR_OK:
                raise Exception(self._get_formatted_error(result[0]))

        theMsg = result[1]
        itsTimeStamp = result[2]

        log.debug("Received a message")

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

        log.debug("Data: %s", msg.data)
        log.debug("Type: %s", type(msg.data))

        result = self.m_objPCANBasic.Write(self.m_PcanHandle, CANMsg)

        sent = result == PCAN_ERROR_OK

        if not sent:
            logging.warning("Failed to send: " + self._get_formatted_error(result))

        return sent

    def flash(self, flash):
        """
        Turn on or off flashing of the device's LED for physical
        identification purposes.
        """
        self.m_objPCANBasic.SetValue(self.channel_info, PCAN_CHANNEL_IDENTIFYING, bool(flash))

    def shutdown(self):
        self.m_objPCANBasic.Uninitialize(self.m_PcanHandle)

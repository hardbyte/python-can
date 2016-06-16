#  Author : Keneth Wagner
#  Copyright (C) 1999-2013  PEAK-System Technik GmbH, Darmstadt
#  more Info at http://www.peak-system.com

import logging
from ctypes import *

from can.interfaces.pcan_constants import *

log = logging.getLogger('can.pcan')
log.setLevel(logging.INFO)


class TPCANMsg(Structure):
    """
    Represents a PCAN message
    """
    _fields_ = [("ID", c_ulong),                # 11/29-bit message identifier
                ("MSGTYPE", TPCANMessageType),  # Type of the message
                ("LEN", c_ubyte),               # Data Length Code of the message (0..8)
                ("DATA", c_ubyte * 8)]          # Data of the message (DATA[0]..DATA[7])


class TPCANTimestamp (Structure):

    """
    Represents a timestamp of a received PCAN message
    Total Microseconds = micros + 1000 * millis + 0xFFFFFFFF * 1000 * millis_overflow
    """
    _fields_ = [("millis", c_ulong),            # Base-value: milliseconds: 0.. 2^32-1
                ("millis_overflow", c_ushort),  # Roll-arounds of millis
                ("micros", c_ushort)]           # Microseconds: 0..999


# ///////////////////////////////////////////////////////////
# PCAN-Basic API function declarations
# ///////////////////////////////////////////////////////////

class PCANBasic:
    """
    PCAN-Basic API class implementation
    """

    def __init__(self):
        """Loads the PCANBasic.dll"""
        self.__m_dllBasic = windll.LoadLibrary("PCANBasic")
        if self.__m_dllBasic is None:
            log.warning("The PCAN-Basic DLL couldn't be loaded!")

    def Initialize(self,
                   Channel,
                   Btr0Btr1,
                   HwType=TPCANType(0),
                   IOPort=c_uint(0),
                   Interrupt=c_ushort(0)):
        """
        Initializes a PCAN Channel

        Parameters:
          Channel  : A TPCANHandle representing a PCAN Channel
          Btr0Btr1 : The speed for the communication (BTR0BTR1 code)
          HwType   : NON PLUG&PLAY: The type of hardware and operation mode
          IOPort   : NON PLUG&PLAY: The I/O address for the parallel port
          Interrupt: NON PLUG&PLAY: Interrupt number of the parallel port

        Returns:
          A TPCANStatus error code
        """
        try:
            res = self.__m_dllBasic.CAN_Initialize(Channel, Btr0Btr1, HwType, IOPort, Interrupt)
            return TPCANStatus(res)
        except:
            log.error("Exception on PCANBasic.Initialize")
            raise

    def Uninitialize(self, Channel):
        """
          Uninitializes one or all PCAN Channels initialized by CAN_Initialize

        Remarks:
          Giving the TPCANHandle value "PCAN_NONEBUS", uninitialize all initialized channels

        Parameters:
          Channel  : A TPCANHandle representing a PCAN Channel

        Returns:
          A TPCANStatus error code
        """
        try:
            res = self.__m_dllBasic.CAN_Uninitialize(Channel)
            return TPCANStatus(res)
        except:
            log.error("Exception on PCANBasic.Uninitialize")
            raise

    def Reset(self, Channel):
        """
          Resets the receive and transmit queues of the PCAN Channel

        Remarks:
          A reset of the CAN controller is not performed

        Parameters:
          Channel  : A TPCANHandle representing a PCAN Channel

        Returns:
          A TPCANStatus error code
        """
        try:
            res = self.__m_dllBasic.CAN_Reset(Channel)
            return TPCANStatus(res)
        except:
            log.error("Exception on PCANBasic.Reset")
            raise

    def GetStatus(self, Channel):
        """
        Gets the current status of a PCAN Channel

        Parameters:
          Channel  : A TPCANHandle representing a PCAN Channel

        Returns:
          A TPCANStatus error code
        """
        try:
            res = self.__m_dllBasic.CAN_GetStatus(Channel)
            return TPCANStatus(res)
        except:
            log.error("Exception on PCANBasic.GetStatus")
            raise

    def Read(self, Channel):
        """
        Reads a CAN message from the receive queue of a PCAN Channel

        Remarks:
          The return value of this method is a 3-tuple, where
          the first value is the result (TPCANStatus) of the method.
          The order of the values are:
          [0]: A TPCANStatus error code
          [1]: A TPCANMsg structure with the CAN message read
          [2]: A TPCANTimestamp structure with the time when a message was read

        Parameters:
          Channel  : A TPCANHandle representing a PCAN Channel

        Returns:
          A tuple with three values
        """
        try:
            msg = TPCANMsg()
            timestamp = TPCANTimestamp()
            res = self.__m_dllBasic.CAN_Read(Channel, byref(msg), byref(timestamp))
            return TPCANStatus(res), msg, timestamp
        except:
            log.error("Exception on PCANBasic.Read")
            raise

    def Write(self, Channel, MessageBuffer):
        """
        Transmits a CAN message

        Parameters:
          Channel      : A TPCANHandle representing a PCAN Channel
          MessageBuffer: A TPCANMsg representing the CAN message to be sent

        Returns:
          A TPCANStatus error code
        """
        try:
            res = self.__m_dllBasic.CAN_Write(Channel, byref(MessageBuffer))
            return TPCANStatus(res)
        except:
            log.error("Exception on PCANBasic.Write")
            raise

    def FilterMessages(self,
                       Channel,
                       FromID,
                       ToID,
                       Mode):
        """
        Configures the reception filter

        Remarks:
          The message filter will be expanded with every call to this function.
          If it is desired to reset the filter, please use the 'SetValue' function.

        Parameters:
          Channel : A TPCANHandle representing a PCAN Channel
          FromID  : A c_ulong value with the lowest CAN ID to be received
          ToID    : A c_ulong value with the highest CAN ID to be received
          Mode    : A TPCANMode representing the message type (Standard, 11-bit
                    identifier, or Extended, 29-bit identifier)

        Returns:
          A TPCANStatus error code
        """
        try:
            res = self.__m_dllBasic.CAN_FilterMessages(Channel, FromID, ToID, Mode)
            return TPCANStatus(res)
        except:
            log.error("Exception on PCANBasic.FilterMessages")
            raise

    def GetValue(self, Channel, Parameter):
        """
        Retrieves a PCAN Channel value

        Remarks:
          Parameters can be present or not according with the kind
          of Hardware (PCAN Channel) being used. If a parameter is not available,
          a PCAN_ERROR_ILLPARAMTYPE error will be returned.

          The return value of this method is a 2-tuple, where
          the first value is the result (TPCANStatus) of the method and
          the second one, the asked value

        Parameters:
          Channel   : A TPCANHandle representing a PCAN Channel
          Parameter : The TPCANParameter parameter to get

        Returns:
          A tuple with 2 values
        """
        try:
            if Parameter == PCAN_API_VERSION or Parameter == PCAN_HARDWARE_NAME or Parameter == PCAN_CHANNEL_VERSION or Parameter == PCAN_LOG_LOCATION or Parameter == PCAN_TRACE_LOCATION:
                mybuffer = create_string_buffer(256)
            else:
                mybuffer = c_int(0)

            res = self.__m_dllBasic.CAN_GetValue(Channel, Parameter, byref(mybuffer), sizeof(mybuffer))
            return TPCANStatus(res), mybuffer.value
        except:
            log.error("Exception on PCANBasic.GetValue")
            raise

    def SetValue(self, Channel, Parameter, Buffer):
        """
        Returns a descriptive text of a given TPCANStatus error
        code, in any desired language

        Remarks:
          Parameters can be present or not according with the kind
          of Hardware (PCAN Channel) being used. If a parameter is not available,
          a PCAN_ERROR_ILLPARAMTYPE error will be returned.

        Parameters:
          Channel      : A TPCANHandle representing a PCAN Channel
          Parameter    : The TPCANParameter parameter to set
          Buffer       : Buffer with the value to be set
          BufferLength : Size in bytes of the buffer

        Returns:
          A TPCANStatus error code
        """
        try:
            if Parameter == PCAN_LOG_LOCATION or Parameter == PCAN_LOG_TEXT or Parameter == PCAN_TRACE_LOCATION:
                mybuffer = create_string_buffer(256)
            else:
                mybuffer = c_int(0)

            mybuffer.value = Buffer
            res = self.__m_dllBasic.CAN_SetValue(Channel, Parameter, byref(mybuffer), sizeof(mybuffer))
            return TPCANStatus(res)
        except:
            log.error("Exception on PCANBasic.SetValue")
            raise

    def GetErrorText(self, Error, Language=0):
        """
        Configures or sets a PCAN Channel value

        Remarks:

          The current languages available for translation are:
          Neutral (0x00), German (0x07), English (0x09),
          Spanish (0x0A), Italian (0x10) and French (0x0C)

        Parameters:
          Error    : A TPCANStatus error code
          Language : Indicates a 'Primary language ID' (Default is Neutral(0))

        Returns:
          A tuple with 2 values, where the first value is the
          result (TPCANStatus) of the method and
          the second one, the error text
        """
        try:
            mybuffer = create_string_buffer(256)
            res = self.__m_dllBasic.CAN_GetErrorText(Error, Language, byref(mybuffer))
            return TPCANStatus(res), mybuffer.value
        except:
            log.error("Exception on PCANBasic.GetErrorText")
            raise

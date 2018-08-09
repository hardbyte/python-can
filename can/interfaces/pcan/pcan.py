#!/usr/bin/env python
# coding: utf-8

"""
Enable basic CAN over a PCAN USB device.
"""

from __future__ import absolute_import, print_function, division

import logging
import sys
import time

import can
from can import CanError, Message, BusABC
from can.bus import BusState
from .basic import *

boottimeEpoch = 0
try:
    import uptime
    import datetime
    boottimeEpoch = (uptime.boottime() - datetime.datetime.utcfromtimestamp(0)).total_seconds()
except:
    boottimeEpoch = 0

try:
    # Try builtin Python 3 Windows API
    from _overlapped import CreateEvent
    from _winapi import WaitForSingleObject, WAIT_OBJECT_0, INFINITE
    HAS_EVENTS = True
except ImportError:
    try:
        # Try pywin32 package
        from win32event import CreateEvent
        from win32event import WaitForSingleObject, WAIT_OBJECT_0, INFINITE
        HAS_EVENTS = True
    except ImportError:
        # Use polling instead
        HAS_EVENTS = False

try:
    # new in 3.3
    timeout_clock = time.perf_counter
except AttributeError:
    # deprecated in 3.3
    timeout_clock = time.clock

# Set up logging
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

    def __init__(self, channel='PCAN_USBBUS1', state=BusState.ACTIVE, bitrate=500000, *args, **kwargs):
        """A PCAN USB interface to CAN.

        On top of the usual :class:`~can.Bus` methods provided,
        the PCAN interface includes the :meth:`~can.interface.pcan.PcanBus.flash`
        and :meth:`~can.interface.pcan.PcanBus.status` methods.

        :param str channel:
            The can interface name. An example would be 'PCAN_USBBUS1'
            Default is 'PCAN_USBBUS1'

        :param can.bus.BusState state:
            BusState of the channel.
            Default is ACTIVE

        :param int bitrate:
            Bitrate of channel in bit/s.
            Default is 500 kbit/s.

        """
        self.channel_info = channel
        pcan_bitrate = pcan_bitrate_objs.get(bitrate, PCAN_BAUD_500K)

        hwtype = PCAN_TYPE_ISA
        ioport = 0x02A0
        interrupt = 11

        self.m_objPCANBasic = PCANBasic()
        self.m_PcanHandle = globals()[channel]

        if state is BusState.ACTIVE or BusState.PASSIVE:
            self._state = state
        else:
            raise ArgumentError("BusState must be Active or Passive")

        result = self.m_objPCANBasic.Initialize(self.m_PcanHandle, pcan_bitrate, hwtype, ioport, interrupt)

        if result != PCAN_ERROR_OK:
            raise PcanError(self._get_formatted_error(result))

        if HAS_EVENTS:
            self._recv_event = CreateEvent(None, 0, 0, None)
            result = self.m_objPCANBasic.SetValue(
                self.m_PcanHandle, PCAN_RECEIVE_EVENT, self._recv_event)
            if result != PCAN_ERROR_OK:
                raise PcanError(self._get_formatted_error(result))

        super(PcanBus, self).__init__(channel=channel, state=state, bitrate=bitrate, *args, **kwargs)

    def _get_formatted_error(self, error):
        """
        Gets the text using the GetErrorText API function.
        If the function call succeeds, the translated error is returned. If it fails,
        a text describing the current error is returned. Multiple errors may
        be present in which case their individual messages are included in the
        return string, one line per error.
        """

        def bits(n):
            """TODO: document"""
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
                    text = stsReturn[1].decode('utf-8', errors='replace')

                strings.append(text)

            complete_text = '\n'.join(strings)
        else:
            complete_text = stsReturn[1].decode('utf-8', errors='replace')

        return complete_text

    def status(self):
        """
        Query the PCAN bus status.

        :rtype: int
        :return: The status code. See values in **basic.PCAN_ERROR_**
        """
        return self.m_objPCANBasic.GetStatus(self.m_PcanHandle)

    def status_is_ok(self):
        """
        Convenience method to check that the bus status is OK
        """
        status = self.status()
        return status == PCAN_ERROR_OK

    def reset(self):
        """
        Command the PCAN driver to reset the bus after an error.
        """
        status = self.m_objPCANBasic.Reset(self.m_PcanHandle)
        return status == PCAN_ERROR_OK

    def _recv_internal(self, timeout):

        if HAS_EVENTS:
            # We will utilize events for the timeout handling
            timeout_ms = int(timeout * 1000) if timeout is not None else INFINITE
        elif timeout is not None:
            # Calculate max time
            end_time = timeout_clock() + timeout

        #log.debug("Trying to read a msg")

        result = None
        while result is None:
            result = self.m_objPCANBasic.Read(self.m_PcanHandle)
            if result[0] == PCAN_ERROR_QRCVEMPTY:
                if HAS_EVENTS:
                    result = None
                    val = WaitForSingleObject(self._recv_event, timeout_ms)
                    if val != WAIT_OBJECT_0:
                        return None, False
                elif timeout is not None and timeout_clock() >= end_time:
                    return None, False
                else:
                    result = None
                    time.sleep(0.001)
            elif result[0] & (PCAN_ERROR_BUSLIGHT | PCAN_ERROR_BUSHEAVY):
                log.warning(self._get_formatted_error(result[0]))
                return None, False
            elif result[0] != PCAN_ERROR_OK:
                raise PcanError(self._get_formatted_error(result[0]))

        theMsg = result[1]
        itsTimeStamp = result[2]

        #log.debug("Received a message")

        bIsRTR = (theMsg.MSGTYPE & PCAN_MESSAGE_RTR.value) == PCAN_MESSAGE_RTR.value
        bIsExt = (theMsg.MSGTYPE & PCAN_MESSAGE_EXTENDED.value) == PCAN_MESSAGE_EXTENDED.value

        dlc = theMsg.LEN
        timestamp = boottimeEpoch + ((itsTimeStamp.micros + 1000 * itsTimeStamp.millis + 0x100000000 * 1000 * itsTimeStamp.millis_overflow) / (1000.0 * 1000.0))

        rx_msg = Message(timestamp=timestamp,
                         arbitration_id=theMsg.ID,
                         extended_id=bIsExt,
                         is_remote_frame=bIsRTR,
                         dlc=dlc,
                         data=theMsg.DATA[:dlc])

        return rx_msg, False

    def send(self, msg, timeout=None):
        if msg.id_type:
            msgType = PCAN_MESSAGE_EXTENDED
        else:
            msgType = PCAN_MESSAGE_STANDARD

        # create a TPCANMsg message structure
        CANMsg = TPCANMsg()

        # configure the message. ID, Length of data, message type and data
        CANMsg.ID = msg.arbitration_id
        CANMsg.LEN = msg.dlc
        CANMsg.MSGTYPE = msgType

        # if a remote frame will be sent, data bytes are not important.
        if msg.is_remote_frame:
            CANMsg.MSGTYPE = msgType.value | PCAN_MESSAGE_RTR.value
        else:
            # copy data
            for i in range(CANMsg.LEN):
                CANMsg.DATA[i] = msg.data[i]

        log.debug("Data: %s", msg.data)
        log.debug("Type: %s", type(msg.data))

        result = self.m_objPCANBasic.Write(self.m_PcanHandle, CANMsg)
        if result != PCAN_ERROR_OK:
            raise PcanError("Failed to send: " + self._get_formatted_error(result))

    def flash(self, flash):
        """
        Turn on or off flashing of the device's LED for physical
        identification purposes.
        """
        self.m_objPCANBasic.SetValue(self.m_PcanHandle, PCAN_CHANNEL_IDENTIFYING, bool(flash))

    def shutdown(self):
        super(PcanBus, self).shutdown()
        self.m_objPCANBasic.Uninitialize(self.m_PcanHandle)

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, new_state):

        self._state = new_state

        if new_state is BusState.ACTIVE:
            self.m_objPCANBasic.SetValue(self.m_PcanHandle, PCAN_LISTEN_ONLY, PCAN_PARAMETER_OFF)

        if new_state is BusState.PASSIVE:
            # When this mode is set, the CAN controller does not take part on active events (eg. transmit CAN messages)
            # but stays in a passive mode (CAN monitor), in which it can analyse the traffic on the CAN bus used by a
            # PCAN channel. See also the Philips Data Sheet "SJA1000 Stand-alone CAN controller".
            self.m_objPCANBasic.SetValue(self.m_PcanHandle, PCAN_LISTEN_ONLY, PCAN_PARAMETER_ON)


class PcanError(CanError):
    """
    TODO: add docs
    """
    pass

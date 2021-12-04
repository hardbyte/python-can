# coding: utf-8

"""
Serial based interface. For example use over serial ports like
"/dev/ttyS1" or "/dev/ttyUSB0" on Linux machines or "COM1" on Windows.
The interface is a simple implementation for uCAN CAN/USB CFUC converter.
"""
from __future__ import absolute_import, division
from typing import Optional

import logging
import struct
from . import can_calc_bittiming

from can import BusABC, Message

logger = logging.getLogger("can.serial")

try:
    import serial
except ImportError:
    logger.warning(
        "You won't be able to use the serial can backend without "
        "the serial module installed!"
    )
    serial = None

ADLC = {
    0: 0x00000000,
    1: 0x00010000,
    2: 0x00020000,
    3: 0x00030000,
    4: 0x00040000,
    5: 0x00050000,
    6: 0x00060000,
    7: 0x00070000,
    8: 0x00080000,
    9: 0x00090000,
    10: 0x000A0000,
    11: 0x000B0000,
    12: 0x000C0000,
    13: 0x000D0000,
    14: 0x000E0000,
    15: 0x000F0000,
}


class cfucBus(BusABC):
    """
    Enable can communication over a ucan CFUC device.

    """

    can_frame_count = 0

    def append_int32(self, dest, source):
        for i in range(0, 4):
            dest.append(source[i])
        return dest

    def consturct_init_frame(
        self,
        IsFD=False,
        IsBRS=False,
        IsAutoRetransmission=False,
        NominalPrescalerValue=1,
        NominalSyncJumpWidthValue=1,
        NominalTimeSeg1Value=13,
        NominalTimeSeg2Value=2,
        DataPrescalerValue=1,
        DataSyncJumpWidthValue=1,
        DataTimeSeg1Value=1,
        DataTimeSeg2Value=1,
    ):

        byte_msg = bytearray()

        UCAN_FD_INIT = struct.pack("<I", int(0x0))
        ClockDivider = struct.pack("<I", int(0x0))
        if IsFD:
            if IsBRS:
                FrameFormat = struct.pack("<I", int(0x00000300))  # fd + brs
            else:
                FrameFormat = struct.pack("<I", int(0x00000200))  # fd
        else:
            FrameFormat = struct.pack("<I", int(0x00000000))  # clasic

        if IsAutoRetransmission == False:
            AutoRetransmission = struct.pack("<I", int(0x00000000))
        else:
            AutoRetransmission = struct.pack("<I", int(0x00000001))

        TransmitPause = struct.pack("<I", int(0x00000000))
        ProtocolException = struct.pack("<I", int(0x00000000))

        NominalPrescaler = struct.pack("<I", NominalPrescalerValue)
        NominalSyncJumpWidth = struct.pack("<I", NominalSyncJumpWidthValue)
        NominalTimeSeg1 = struct.pack("<I", NominalTimeSeg1Value)
        NominalTimeSeg2 = struct.pack("<I", NominalTimeSeg2Value)
        DataPrescaler = struct.pack("<I", DataPrescalerValue)
        DataSyncJumpWidth = struct.pack("<I", DataSyncJumpWidthValue)
        DataTimeSeg1 = struct.pack("<I", DataTimeSeg1Value)
        DataTimeSeg2 = struct.pack("<I", DataTimeSeg2Value)

        StdFiltersNbr = struct.pack("<I", int(0x00000000))
        ExtFiltersNbr = struct.pack("<I", int(0x00000000))
        TxFifoQueueMode = struct.pack("<I", int(0x00000000))

        byte_msg = self.append_int32(byte_msg, UCAN_FD_INIT)
        byte_msg = self.append_int32(byte_msg, ClockDivider)
        byte_msg = self.append_int32(byte_msg, FrameFormat)
        byte_msg = self.append_int32(byte_msg, AutoRetransmission)
        byte_msg = self.append_int32(byte_msg, TransmitPause)
        byte_msg = self.append_int32(byte_msg, ProtocolException)
        byte_msg = self.append_int32(byte_msg, NominalPrescaler)
        byte_msg = self.append_int32(byte_msg, NominalSyncJumpWidth)
        byte_msg = self.append_int32(byte_msg, NominalTimeSeg1)
        byte_msg = self.append_int32(byte_msg, NominalTimeSeg2)
        byte_msg = self.append_int32(byte_msg, DataPrescaler)
        byte_msg = self.append_int32(byte_msg, DataSyncJumpWidth)
        byte_msg = self.append_int32(byte_msg, DataTimeSeg1)
        byte_msg = self.append_int32(byte_msg, DataTimeSeg2)
        byte_msg = self.append_int32(byte_msg, StdFiltersNbr)
        byte_msg = self.append_int32(byte_msg, ExtFiltersNbr)
        byte_msg = self.append_int32(byte_msg, TxFifoQueueMode)

        return byte_msg

    """
    Enable basic can communication over a serial.

    .. note:: See :meth:`can.interfaces.serial.SerialBus._recv_internal`
              for some special semantics.

    """

    def __init__(
        self,
        channel: str,
        CANBaudRate: int,
        IsFD: Optional[bool] = False,
        FDDataBaudRate: Optional[int] = 0,
        IsBRS: Optional[bool] = False,
        IsAutoRetransmission: Optional[bool] = False,
        NominalPrescalerValue: Optional[int] = None,
        NominalSyncJumpWidthValue: Optional[int] = None,
        NominalTimeSeg1Value: Optional[int] = None,
        NominalTimeSeg2Value: Optional[int] = None,
        DataPrescalerValue: Optional[int] = None,
        DataSyncJumpWidthValue: Optional[int] = None,
        DataTimeSeg1Value: Optional[int] = None,
        DataTimeSeg2Value: Optional[int] = None,
        *args,
        **kwargs
    ):
        """
        :param str channel:
            The serial device to open. For example "/dev/ttyS1" or
            "/dev/ttyUSB0" on Linux or "COM1" on Windows systems.

        :param int CANBaudRate for ID:
            Baud rate of CAN device in bit/s .

        :param bool IsFD:
            Is CAN frame FD (default false).

        :param bool FDDataBaudRate:
            Baud Rate for data segment for FD-CAN frame (default 0).

        :param bool IsBRS:
            Enable bit rate switching for FD-CAN frame (default false).

        :param boot IsAutoRetransmission:
            Enbale auto restramission on tx

        :param int NominalPrescalerValue, NominalSyncJumpWidthValue, NominalTimeSeg1Value, NominalTimeSeg2Value
            .. warning::
                USED ONLY WHEN CANBuadRate is set to 0.
            CAN Perfierial Timming parameters for ID


        :param int DataPrescalerValue, DataSyncJumpWidthValue, DataTimeSeg1Value, DataTimeSeg2Value
            .. warning::
                USED ONLY WHEN CANBuadRate is set to 0.
            CAN Perfierial Timming parameters for ID
        """

        if not channel:
            raise ValueError("Must specify a serial port.")

        self.channel_info = "Serial interface: " + channel
        self.ser = serial.serial_for_url(
            channel, baudrate=115200, timeout=0.1, rtscts=False
        )

        self.can_frame_count = 0

        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()

        if CANBaudRate != 0:
            bt = can_calc_bittiming.bt()
            bt.bitrate = CANBaudRate
            btc = can_calc_bittiming.btc()
            bt = can_calc_bittiming.CAN_CALC_BITTIMING(bt, btc)

            NominalTimeSeg1Value = bt.phase_seg1 + bt.prop_seg
            NominalTimeSeg2Value = bt.phase_seg2
            NominalPrescalerValue = bt.brp
            NominalSyncJumpWidthValue = bt.sjw

        if FDDataBaudRate != 0:
            bt = can_calc_bittiming.bt()
            bt.bitrate = FDDataBaudRate
            btc = can_calc_bittiming.btc()
            bt = can_calc_bittiming.CAN_CALC_BITTIMING(bt, btc)

            DataTimeSeg1Value = bt.phase_seg1 + bt.prop_seg
            DataTimeSeg2Value = bt.phase_seg2
            DataPrescalerValue = bt.brp
            DataSyncJumpWidthValue = bt.sjw

        frame = self.consturct_init_frame(
            IsFD,
            IsBRS,
            IsAutoRetransmission,
            NominalPrescalerValue,
            NominalSyncJumpWidthValue,
            NominalTimeSeg1Value,
            NominalTimeSeg2Value,
            DataPrescalerValue,
            DataSyncJumpWidthValue,
            DataTimeSeg1Value,
            DataTimeSeg2Value,
        )

        self.ser.write(frame)

        # super(cfucBus, self).__init__(channel=channel, *args, **kwargs)

    def shutdown(self):
        """
        Close the serial interface.
        """
        self.ser.close()

    def send(self, msg, timeout=None):
        """
        Send a message over the serial device.

        :param can.Message msg:
            Message to send.

            .. note:: If the timestamp is a value it will be ignored

        :param timeout:
            This parameter will be ignored. The timeout value of the channel is
            used instead.

        """

        UCAN_FD_TX = struct.pack("<I", int(0x2))
        try:
            a_id = struct.pack("<I", msg.arbitration_id)
        except struct.error:
            raise ValueError("Arbitration Id is out of range")
        a_ex = b"\x00\x00\x00\x40" if (msg.is_extended_id) else b"\x00\x00\x00\x00"
        a_rmt = b"\x00\x00\x00\x20" if (msg.is_remote_frame) else b"\x00\x00\x00\x00"

        a_dlc = struct.pack("<I", int(ADLC[msg.dlc]))

        # copy all structs to byte stream
        byte_msg = bytearray()
        # UCAN_FRAME_TYPE frame_type; /*!< Frame type is @ref UCAN_FD_TX.*/
        for i in range(0, 4):
            byte_msg.append(UCAN_FD_TX[i])
        # FDCAN_TxHeaderTypeDef can_tx_header; /*!< FDCAN Tx event FIFO structure definition @ref FDCAN_TxHeaderTypeDef.*/
        for i in range(0, 4):
            byte_msg.append(a_id[i])
        for i in range(0, 4):
            byte_msg.append(a_ex[i])
        for i in range(0, 4):
            byte_msg.append(a_rmt[i])
        for i in range(0, 4):
            byte_msg.append(a_dlc[i])

        if msg.error_state_indicator == False:
            # ErrorStateIndicator FDCAN_ESI_PASSIVE
            byte_msg.extend(b"\x00\x00\x00\x00")
        else:
            # ErrorStateIndicator FDCAN_ESI_ACTIVE
            byte_msg.extend(b"\x00\x00\x00\x80")

        if msg.bitrate_switch == False:
            byte_msg.extend(b"\x00\x00\x00\x00")  # BitRateSwitch FDCAN_BRS_OFF
        else:
            byte_msg.extend(b"\x00\x00\x10\x00")  # BitRateSwitch FDCAN_BRS_ON

        if msg.is_fd == False:
            byte_msg.extend(b"\x00\x00\x00\x00")  # FDFormat FDCAN_CLASSIC_CAN
        else:
            byte_msg.extend(b"\x00\x00\x20\x00")  # FDFormat FDCAN_FD_CAN

        byte_msg.extend(b"\x00\x00\x00\x00")  # TxEventFifoControl
        byte_msg.extend(b"\x00\x00\x00\x00")  # MessageMarker

        # uint8_t can_data[64]; /* Data CAN buffer */
        for i in range(0, msg.dlc):
            byte_msg.append(msg.data[i])
        for i in range(msg.dlc, 64):
            byte_msg.extend(b"\x00")
        self.ser.write(byte_msg)

    def _recv_internal(self, timeout):
        """
        Read a message from the serial device.

        :param timeout:

            .. warning::
                This parameter will be ignored. The timeout value of the channel is used.

        :returns:
            Received message and False (because not filtering as taken place).

            .. warning::
                Flags like is_extended_id, is_remote_frame and is_error_frame
                will not be set over this function, the flags in the return
                message are the default values.

        :rtype:
            can.Message, bool
        """
        if self.can_frame_count == 0:
            # ser.read can return an empty string
            # or raise a SerialException
            try:
                rx_byte = self.ser.read(4)
                rx_byte = (struct.unpack("<I", rx_byte))[0]
            except serial.SerialException:
                return None, False
            if rx_byte == 0x06:  # UCAN_FD_RX:
                s = bytearray(self.ser.read(4))
                self.can_frame_count = (struct.unpack("<I", s))[0]
            # else
            if (self.can_frame_count > 0) & (self.can_frame_count < 10):
                self.can_frame_count = self.can_frame_count - 1
                s = bytearray(self.ser.read(4))
                arb_id = (struct.unpack("<I", s))[0]  # Identifier
                s = bytearray(self.ser.read(8))  # IdType #RxFrameType
                s = bytearray(self.ser.read(4))  # DataLength
                len = (struct.unpack("<I", s))[0]
                dlc = list(ADLC.values()).index(len)
                s = bytearray(self.ser.read(4))  # ErrorStateIndicator
                s = bytearray(self.ser.read(4))  # BitRateSwitch
                s = bytearray(self.ser.read(4))  # FDFormat
                s = bytearray(self.ser.read(4))  # RxTimestamp
                timestamp = (struct.unpack("<I", s))[0]
                s = bytearray(self.ser.read(4))  # FilterIndex
                s = bytearray(self.ser.read(4))  # IsFilterMatchingFrame
                data = bytearray(self.ser.read(64))  # can_data
                # packed_flags_and_error_counters
                s = bytearray(self.ser.read(4))

                msg = Message(
                    timestamp=timestamp / 1000,
                    arbitration_id=arb_id,
                    dlc=dlc,
                    data=data,
                )
                return msg, False
            else:
                self.can_frame_count = 0
                return None, False

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
import enum
from can import BusABC, Message

from can import (
    CanInterfaceNotImplementedError,
    CanInitializationError,
    CanOperationError,
    CanTimeoutError,
)

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

class UCAN_FRAME_TYPE(enum.Enum):
   UCAN_FD_INIT = 0 # init CAN with all parameters, open in mode specified in init data. Frame direction USB->CAN*/
   UCAN_FD_DEINIT = 1 # deinit CAN, close CAN connection. Frame direction USB->CAN*/
   UCAN_FD_TX = 2 # send new frame on CAN network. Frame direction USB->CAN  */
   UCAN_FD_SAVE_CONFIG = 3 # saves CAN config to NVM USB->CAN*/
   UCAN_FD_GO_TO_BOOTLOADER = 4 # go to USB bootloader USB->CAN*/
   UCAN_FD_GET_CAN_STATUS = 5 # request status USB->CAN*/
   UCAN_FD_RX = 6 # new CAN frame received on network. Frame direction CAN->USB*/
   UCAN_FD_ACK = 7 # gets CAN status from CONVERTER. Also ACK resposne for all frames form USB. Frame direction CAN->USB */


class cfucBus(BusABC):
    """
    Enable can communication over a ucan CFUC device.

    """

    def _consturct_init_frame(
        self,
        IsFD=False,
        IsBRS=False,
        IsAutoRetransmission=True,
        NominalPrescaler: int = 90,
        NominalSyncJumpWidthValue: int = 128,
        NominalTimeSeg1Value: int = 13,
        NominalTimeSeg2Value: int = 2,
        DataPrescalerValue: int = 1,
        DataSyncJumpWidthValue: int = 1,
        DataTimeSeg1Value: int = 1,
        DataTimeSeg2Value: int = 1,
    ):
        """
        Generate an initialization frame for CFUC device.

        """

        FrameType = struct.pack("<I", UCAN_FRAME_TYPE.UCAN_FD_INIT.value)
        ClockDivider = struct.pack("<I", int(0x0))

        if IsFD:
            if IsBRS:
                FrameFormat = struct.pack("<I", int(0x00000300))  # fd + brs
            else:
                FrameFormat = struct.pack("<I", int(0x00000200))  # fd
        else:
            FrameFormat = bytearray(b'\x00\x00\x00\x00')  # clasic

        if IsAutoRetransmission == False:
            AutoRetransmission = bytearray(b'\x00')
        else:
            AutoRetransmission = bytearray(b'\x01')

        byte_msg =  bytearray(FrameType)  #UCAN_FD_INIT
        byte_msg += ClockDivider  #ClockDivider
        byte_msg += FrameFormat #FrameFormat
        byte_msg += struct.pack("<I", int(0)) #Mode
        byte_msg += AutoRetransmission #AutoRetransmission
        byte_msg += bytearray(b'\x00') #TransmitPause
        byte_msg += bytearray(b'\x00') #ProtocolException
        byte_msg += bytearray(b'\x00') #bug - empty byte, fillup byte
        byte_msg += struct.pack("<I", NominalPrescaler) #NominalPrescaler
        byte_msg += struct.pack("<I", NominalSyncJumpWidthValue) #NominalSyncJumpWidth
        byte_msg += struct.pack("<I", NominalTimeSeg1Value) #NominalTimeSeg1
        byte_msg += struct.pack("<I", NominalTimeSeg2Value) #NominalTimeSeg2
        byte_msg += struct.pack("<I", int(1)) #DataPrescaler
        byte_msg += struct.pack("<I", int(1)) #DataSyncJumpWidth
        byte_msg += struct.pack("<I", int(1)) #DataTimeSeg1
        byte_msg += struct.pack("<I", int(1)) #DataTimeSeg2
        byte_msg += bytearray(b'\x00\x00\x00\x00') #StdFiltersNbr
        byte_msg += bytearray(b'\x00\x00\x00\x00') #ExtFiltersNbr
        byte_msg += bytearray(b'\x00\x00\x00\x00') #TxFifoQueueMode

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

        init_frame = self._consturct_init_frame(
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

        self.ser.write(init_frame)

        super().__init__(channel, *args, **kwargs)


    def shutdown(self):
        """
        Close the serial interface.
        """
        super().shutdown()
        self.ser.close()


    def send(self, msg: Message, timeout=None):
        """
        Send a message over the serial device.

        :param can.Message msg:
            Message to send.

            .. note:: If the timestamp is a value it will be ignored

        :param timeout:
            This parameter will be ignored. The timeout value of the channel is
            used instead.

        """

        FrameType = struct.pack("<I", UCAN_FRAME_TYPE.UCAN_FD_TX.value)
        try:
            a_id = struct.pack("<I", msg.arbitration_id)
        except struct.error:
            raise ValueError("Arbitration Id is out of range")

        a_ex = bytearray(b'\x00\x00\x00\x40') if (msg.is_extended_id) else bytearray(b'\x00\x00\x00\x00')
        a_rmt = bytearray(b'\x00\x00\x00\x20') if (msg.is_remote_frame) else bytearray(b'\x00\x00\x00\x00')

        a_dlc = struct.pack("<I", int(ADLC[msg.dlc]))

        # copy all structs to byte stream
        # UCAN_FRAME_TYPE frame_type; /*!< Frame type is @ref UCAN_FD_TX.*/
        byte_msg = bytearray(FrameType)
        # FDCAN_TxHeaderTypeDef can_tx_header; /*!< FDCAN Tx event FIFO structure definition @ref FDCAN_TxHeaderTypeDef.*/
        byte_msg += a_id
        byte_msg += a_ex
        byte_msg += a_rmt
        byte_msg += a_dlc

        if msg.error_state_indicator == False:
            # ErrorStateIndicator FDCAN_ESI_PASSIVE
            byte_msg += bytearray(b'\x00\x00\x00\x00')
        else:
            # ErrorStateIndicator FDCAN_ESI_ACTIVE
            byte_msg += bytearray(b'\x00\x00\x00\x80')

        if msg.bitrate_switch == False:
            byte_msg += bytearray(b'\x00\x00\x00\x00')  # BitRateSwitch FDCAN_BRS_OFF
        else:
            byte_msg += bytearray(b'\x00\x00\x10\x00')  # BitRateSwitch FDCAN_BRS_ON

        if msg.is_fd == False:
            byte_msg += bytearray(b'\x00\x00\x00\x00')  # FDFormat FDCAN_CLASSIC_CAN
        else:
            byte_msg += bytearray(b'\x00\x00\x20\x00')  # FDFormat FDCAN_FD_CAN

        byte_msg += bytearray(b'\x00\x00\x00\x00')  # TxEventFifoControl
        byte_msg += bytearray(b'\x00\x00\x00\x00')  # MessageMarker

        # uint8_t can_data[64]; /* Data CAN buffer */
        for i in range(0, msg.dlc):
            byte_msg.append(msg.data[i])

        for i in range(msg.dlc, 64):
            byte_msg += bytearray(b'\x00')
            
        self.ser.write(byte_msg)


    def _read(self, length):
        rx_buffer = bytearray(self.ser.read(length))
        rx_length = len(rx_buffer)

        if length == rx_length:
            result = (struct.unpack("<I", rx_buffer))[0]
            return result
        else:
            return -1


    def _read_rx_frame(self) -> Message:
        # read FDCAN_RxHeaderTypeDef structure
        can_rx_header_Identifier = self._read(4)
        can_rx_header_IdType = self._read(4)
        can_rx_header_RxFrameType = self._read(4)
        can_rx_header_DataLength = self._read(4)
        can_rx_header_ErrorStateIndicator = self._read(4)
        can_rx_header_BitRateSwitch = self._read(4)
        can_rx_header_FDFormat = self._read(4)
        can_rx_header_RxTimestamp = self._read(4)
        can_rx_header_FilterIndex = self._read(4)
        can_rx_header_IsFilterMatchingFrame = self._read(4)

        #read Data CAN buffer
        can_data = bytearray(self.ser.read(64))

        #read Flasg and Errors
        packed_flags_and_error_counters = self._read(4)        
        
        dlc = list(ADLC.values()).index(can_rx_header_DataLength)

        msg = Message(
            timestamp = can_rx_header_RxTimestamp / 1000,
            arbitration_id = can_rx_header_Identifier,
            dlc = dlc,
            data = can_data,
            is_fd = True if can_rx_header_FDFormat else False,
            is_extended_id = True if can_rx_header_IdType else False,
            bitrate_switch = True if can_rx_header_BitRateSwitch else False,
            is_remote_frame = True if can_rx_header_RxFrameType else False,
            error_state_indicator = True if can_rx_header_ErrorStateIndicator else False,
        )
        return msg


    def _read_tx_frame(self) -> Message:
        # read FDCAN_TxHeaderTypeDef structure
        can_tx_header_Identifier = self._read(4)
        can_tx_header_IdType = self._read(4)
        can_tx_header_TxFrameType = self._read(4)
        can_tx_header_DataLength = self._read(4)
        can_tx_header_ErrorStateIndicator = self._read(4)
        can_tx_header_BitRateSwitch = self._read(4)
        can_tx_header_FDFormat = self._read(4)
        can_tx_header_TxEventFifoControl = self._read(4)
        can_tx_header_MessageMarker = self._read(4)

        can_data = bytearray(self.ser.read(64))

        dlc = list(ADLC.values()).index(can_tx_header_DataLength)

        msg = Message(
            arbitration_id = can_tx_header_Identifier,
            dlc = dlc,
            data = can_data,
            is_fd = True if can_tx_header_FDFormat else False,
            is_extended_id = True if can_tx_header_IdType else False,
            bitrate_switch= True if can_tx_header_BitRateSwitch else False,
            is_remote_frame= True if can_tx_header_TxFrameType else False,
            error_state_indicator = True if can_tx_header_ErrorStateIndicator else False,
        )
        return msg, False


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
        frame_type = self._read(4) # read frame type 

        if frame_type == UCAN_FRAME_TYPE.UCAN_FD_TX.value:
            results = self._read_tx_frame()
            return results, False
            
        elif frame_type == UCAN_FRAME_TYPE.UCAN_FD_RX.value:
            results = list()
            can_frame_count = self._read(4) # read frame count

            for i in range(can_frame_count):
                results.append(self._read_rx_frame())

            return tuple(results), False
        
        elif frame_type == -1:
            return None, False

        # else:
        #     print("ERROR", frame_type)

        return None, False
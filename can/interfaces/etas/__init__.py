import ctypes
import time
from typing import Dict, List, Optional, Tuple

import can
from ...exceptions import CanInitializationError, CanOperationError
from .boa import *


class EtasBus(can.BusABC):
    def __init__(
        self,
        channel: str,
        can_filters: Optional[can.typechecking.CanFilters] = None,
        receive_own_messages: bool = False,
        bitrate: int = 1000000,
        fd: bool = True,
        data_bitrate: int = 2000000,
        **kwargs: object,
    ):
        self.receive_own_messages = receive_own_messages

        nodeRange = CSI_NodeRange(CSI_NODE_MIN, CSI_NODE_MAX)
        self.tree = ctypes.POINTER(CSI_Tree)()
        ec = CSI_CreateProtocolTree(
            ctypes.c_char_p(b""), nodeRange, ctypes.byref(self.tree)
        )
        if ec != 0x0:
            raise CanInitializationError(
                f"CSI_CreateProtocolTree failed with error 0x{ec:X}"
            )

        oci_can_v = BOA_Version(1, 4, 0, 0)

        # Common

        self.ctrl = OCI_ControllerHandle()
        ec = OCI_CreateCANControllerNoSearch(
            channel.encode(),
            ctypes.byref(oci_can_v),
            self.tree,
            ctypes.byref(self.ctrl),
        )
        if ec != 0x0:
            raise CanInitializationError(
                f"OCI_CreateCANControllerNoSearch failed with error 0x{ec:X}"
            )

        ctrlConf = OCI_CANConfiguration()
        ctrlConf.baudrate = bitrate
        ctrlConf.samplePoint = 80
        ctrlConf.samplesPerBit = OCI_CAN_THREE_SAMPLES_PER_BIT
        ctrlConf.BTL_Cycles = 10
        ctrlConf.SJW = 1
        ctrlConf.syncEdge = OCI_CAN_SINGLE_SYNC_EDGE
        ctrlConf.physicalMedia = OCI_CAN_MEDIA_HIGH_SPEED
        if receive_own_messages:
            ctrlConf.selfReceptionMode = OCI_SELF_RECEPTION_ON
        else:
            ctrlConf.selfReceptionMode = OCI_SELF_RECEPTION_OFF
        ctrlConf.busParticipationMode = OCI_BUSMODE_ACTIVE

        if fd:
            ctrlConf.canFDEnabled = True
            ctrlConf.canFDConfig.dataBitRate = data_bitrate
            ctrlConf.canFDConfig.dataBTL_Cycles = 10
            ctrlConf.canFDConfig.dataSamplePoint = 80
            ctrlConf.canFDConfig.dataSJW = 1
            ctrlConf.canFDConfig.flags = 0
            ctrlConf.canFDConfig.canFdTxConfig = OCI_CANFDTX_USE_CAN_AND_CANFD_FRAMES
            ctrlConf.canFDConfig.canFdRxConfig.canRxMode = (
                OCI_CAN_RXMODE_CAN_FRAMES_USING_CAN_MESSAGE
            )
            ctrlConf.canFDConfig.canFdRxConfig.canFdRxMode = (
                OCI_CANFDRXMODE_CANFD_FRAMES_USING_CANFD_MESSAGE
            )

        ctrlProp = OCI_CANControllerProperties()
        ctrlProp.mode = OCI_CONTROLLER_MODE_RUNNING

        ec = OCI_OpenCANController(
            self.ctrl, ctypes.byref(ctrlConf), ctypes.byref(ctrlProp)
        )
        if ec != 0x0 and ec != 0x40004000:  # accept BOA_WARN_PARAM_ADAPTED
            raise CanInitializationError(
                f"OCI_OpenCANController failed with error 0x{ec:X}"
            )

        # RX

        rxQConf = OCI_CANRxQueueConfiguration()
        rxQConf.onFrame.function = ctypes.cast(None, OCI_CANRxCallbackFunctionSingleMsg)
        rxQConf.onFrame.userData = None
        rxQConf.onEvent.function = ctypes.cast(None, OCI_CANRxCallbackFunctionSingleMsg)
        rxQConf.onEvent.userData = None
        if receive_own_messages:
            rxQConf.selfReceptionMode = OCI_SELF_RECEPTION_ON
        else:
            rxQConf.selfReceptionMode = OCI_SELF_RECEPTION_OFF
        self.rxQueue = OCI_QueueHandle()
        ec = OCI_CreateCANRxQueue(
            self.ctrl, ctypes.byref(rxQConf), ctypes.byref(self.rxQueue)
        )
        if ec != 0x0:
            raise CanInitializationError(
                f"OCI_CreateCANRxQueue failed with error 0x{ec:X}"
            )

        self._oci_filters = None
        self.filters = can_filters

        # TX

        txQConf = OCI_CANTxQueueConfiguration()
        txQConf.reserved = 0
        self.txQueue = OCI_QueueHandle()
        ec = OCI_CreateCANTxQueue(
            self.ctrl, ctypes.byref(txQConf), ctypes.byref(self.txQueue)
        )
        if ec != 0x0:
            raise CanInitializationError(
                f"OCI_CreateCANTxQueue failed with error 0x{ec:X}"
            )

        # Common

        timerCapabilities = OCI_TimerCapabilities()
        ec = OCI_GetTimerCapabilities(self.ctrl, ctypes.byref(timerCapabilities))
        if ec != 0x0:
            raise CanInitializationError(
                f"OCI_GetTimerCapabilities failed with error 0x{ec:X}"
            )
        self.tickFrequency = timerCapabilities.tickFrequency  # clock ticks per second

        # all timestamps are hardware timestamps relative to the CAN device powerup
        # calculate an offset to make them relative to epoch
        now = OCI_Time()
        ec = OCI_GetTimerValue(self.ctrl, ctypes.byref(now))
        if ec != 0x0:
            raise CanInitializationError(
                f"OCI_GetTimerValue failed with error 0x{ec:X}"
            )
        self.timeOffset = time.time() - (float(now.value) / self.tickFrequency)

        self.channel_info = channel

    def _recv_internal(
        self, timeout: Optional[float]
    ) -> Tuple[Optional[can.Message], bool]:
        canMessages = (ctypes.POINTER(OCI_CANMessageEx) * 1)()

        m = OCI_CANMessageEx()
        canMessages[0].contents = m

        count = ctypes.c_uint32()
        remaining = ctypes.c_uint32()
        if timeout is not None:
            t = OCI_Time(round(timeout * self.tickFrequency))
        else:
            t = OCI_NO_TIME
        ec = OCI_ReadCANDataEx(
            self.rxQueue,
            t,
            canMessages,
            1,
            ctypes.byref(count),
            ctypes.byref(remaining),
        )
        if ec != 0x0:
            text = ctypes.create_string_buffer(500)
            OCI_GetError(self.ctrl, ec, text, 500)
            raise CanOperationError(f"OCI_ReadCANDataEx failed with error 0x{ec:X}")

        msg = None

        if count.value != 0:
            m = canMessages[0].contents
            if m.type == OCI_CANFDRX_MESSAGE.value:
                msg = can.Message(
                    timestamp=float(m.data.canFDRxMessage.timeStamp)
                    / self.tickFrequency
                    + self.timeOffset,
                    arbitration_id=m.data.canFDRxMessage.frameID,
                    is_extended_id=bool(
                        m.data.canFDRxMessage.flags & OCI_CAN_MSG_FLAG_EXTENDED
                    ),
                    is_remote_frame=bool(
                        m.data.canFDRxMessage.flags & OCI_CAN_MSG_FLAG_REMOTE_FRAME
                    ),
                    # is_error_frame=False,
                    # channel=None,
                    dlc=m.data.canFDRxMessage.size,
                    data=m.data.canFDRxMessage.data[0 : m.data.canFDRxMessage.size],
                    is_fd=True,
                    is_rx=not bool(
                        m.data.canFDRxMessage.flags & OCI_CAN_MSG_FLAG_SELFRECEPTION
                    ),
                    bitrate_switch=bool(
                        m.data.canFDRxMessage.flags & OCI_CAN_MSG_FLAG_FD_DATA_BIT_RATE
                    ),
                    # error_state_indicator=False,
                    # check=False,
                )
            elif m.type == OCI_CAN_RX_MESSAGE.value:
                msg = can.Message(
                    timestamp=float(m.data.rxMessage.timeStamp) / self.tickFrequency
                    + self.timeOffset,
                    arbitration_id=m.data.rxMessage.frameID,
                    is_extended_id=bool(
                        m.data.rxMessage.flags & OCI_CAN_MSG_FLAG_EXTENDED
                    ),
                    is_remote_frame=bool(
                        m.data.rxMessage.flags & OCI_CAN_MSG_FLAG_REMOTE_FRAME
                    ),
                    # is_error_frame=False,
                    # channel=None,
                    dlc=m.data.rxMessage.dlc,
                    data=m.data.rxMessage.data[0 : m.data.rxMessage.dlc],
                    # is_fd=False,
                    is_rx=not bool(
                        m.data.rxMessage.flags & OCI_CAN_MSG_FLAG_SELFRECEPTION
                    ),
                    # bitrate_switch=False,
                    # error_state_indicator=False,
                    # check=False,
                )

        return (msg, True)

    def send(self, msg: can.Message, timeout: Optional[float] = None) -> None:
        canMessages = (ctypes.POINTER(OCI_CANMessageEx) * 1)()

        m = OCI_CANMessageEx()

        if msg.is_fd:
            m.type = OCI_CANFDTX_MESSAGE
            m.data.canFDTxMessage.frameID = msg.arbitration_id
            m.data.canFDTxMessage.flags = 0
            if msg.is_extended_id:
                m.data.canFDTxMessage.flags |= OCI_CAN_MSG_FLAG_EXTENDED
            if msg.is_remote_frame:
                m.data.canFDTxMessage.flags |= OCI_CAN_MSG_FLAG_REMOTE_FRAME
            m.data.canFDTxMessage.flags |= OCI_CAN_MSG_FLAG_FD_DATA
            if msg.bitrate_switch:
                m.data.canFDTxMessage.flags |= OCI_CAN_MSG_FLAG_FD_DATA_BIT_RATE
            m.data.canFDTxMessage.size = msg.dlc
            m.data.canFDTxMessage.data = tuple(msg.data)
        else:
            m.type = OCI_CAN_TX_MESSAGE
            m.data.txMessage.frameID = msg.arbitration_id
            m.data.txMessage.flags = 0
            if msg.is_extended_id:
                m.data.txMessage.flags |= OCI_CAN_MSG_FLAG_EXTENDED
            if msg.is_remote_frame:
                m.data.txMessage.flags |= OCI_CAN_MSG_FLAG_REMOTE_FRAME
            m.data.txMessage.dlc = msg.dlc
            m.data.txMessage.data = tuple(msg.data)

        canMessages[0].contents = m

        ec = OCI_WriteCANDataEx(self.txQueue, OCI_NO_TIME, canMessages, 1, None)
        if ec != 0x0:
            raise CanOperationError(f"OCI_WriteCANDataEx failed with error 0x{ec:X}")

    def _apply_filters(self, filters: Optional[can.typechecking.CanFilters]) -> None:
        if self._oci_filters:
            ec = OCI_RemoveCANFrameFilterEx(self.rxQueue, self._oci_filters, 1)
            if ec != 0x0:
                raise CanOperationError(
                    f"OCI_RemoveCANFrameFilterEx failed with error 0x{ec:X}"
                )

        # "accept all" filter
        if filters is None:
            filters = [{"can_id": 0x0, "can_mask": 0x0}]

        self._oci_filters = (ctypes.POINTER(OCI_CANRxFilterEx) * len(filters))()

        for i, filter in enumerate(filters):
            f = OCI_CANRxFilterEx()
            f.frameIDValue = filter["can_id"]
            f.frameIDMask = filter["can_mask"]
            f.tag = 0
            f.flagsValue = 0
            if self.receive_own_messages:
                # mask out the SR bit, i.e. ignore the bit -> receive all
                f.flagsMask = 0
            else:
                # enable the SR bit in the mask. since the bit is 0 in flagsValue -> do not self-receive
                f.flagsMask = OCI_CAN_MSG_FLAG_SELFRECEPTION
            if filter.get("extended"):
                f.flagsValue |= OCI_CAN_MSG_FLAG_EXTENDED
                f.flagsMask |= OCI_CAN_MSG_FLAG_EXTENDED
            self._oci_filters[i].contents = f

        ec = OCI_AddCANFrameFilterEx(
            self.rxQueue, self._oci_filters, len(self._oci_filters)
        )
        if ec != 0x0:
            raise CanOperationError(
                f"OCI_AddCANFrameFilterEx failed with error 0x{ec:X}"
            )

    def flush_tx_buffer(self) -> None:
        ec = OCI_ResetQueue(self.txQueue)
        if ec != 0x0:
            raise CanOperationError(f"OCI_ResetQueue failed with error 0x{ec:X}")

    def shutdown(self) -> None:
        # Cleanup TX
        if self.txQueue:
            ec = OCI_DestroyCANTxQueue(self.txQueue)
            if ec != 0x0:
                raise CanOperationError(
                    f"OCI_DestroyCANTxQueue failed with error 0x{ec:X}"
                )
            self.txQueue = None

        # Cleanup RX
        if self.rxQueue:
            ec = OCI_DestroyCANRxQueue(self.rxQueue)
            if ec != 0x0:
                raise CanOperationError(
                    f"OCI_DestroyCANRxQueue failed with error 0x{ec:X}"
                )
            self.rxQueue = None

        # Cleanup common
        if self.ctrl:
            ec = OCI_CloseCANController(self.ctrl)
            if ec != 0x0:
                raise CanOperationError(
                    f"OCI_CloseCANController failed with error 0x{ec:X}"
                )
            ec = OCI_DestroyCANController(self.ctrl)
            if ec != 0x0:
                raise CanOperationError(
                    f"OCI_DestroyCANController failed with error 0x{ec:X}"
                )
            self.ctrl = None

        if self.tree:
            ec = CSI_DestroyProtocolTree(self.tree)
            if ec != 0x0:
                raise CanOperationError(
                    f"CSI_DestroyProtocolTree failed with error 0x{ec:X}"
                )
            self.tree = None

    @property
    def state(self) -> can.BusState:
        status = OCI_CANControllerStatus()
        ec = OCI_GetCANControllerStatus(self.ctrl, ctypes.byref(status))
        if ec != 0x0:
            raise CanOperationError(
                f"OCI_GetCANControllerStatus failed with error 0x{ec:X}"
            )
        if status.stateCode & OCI_CAN_STATE_ACTIVE:
            return can.BusState.ACTIVE
        elif status.stateCode & OCI_CAN_STATE_PASSIVE:
            return can.BusState.PASSIVE

    @state.setter
    def state(self, new_state: can.BusState) -> None:
        # disabled, OCI_AdaptCANConfiguration does not allow changing the bus mode
        # if new_state == can.BusState.ACTIVE:
        #     self.ctrlConf.busParticipationMode = OCI_BUSMODE_ACTIVE
        # else:
        #     self.ctrlConf.busParticipationMode = OCI_BUSMODE_PASSIVE
        # ec = OCI_AdaptCANConfiguration(self.ctrl, ctypes.byref(self.ctrlConf))
        # if ec != 0x0:
        #     raise CanOperationError(f"OCI_AdaptCANConfiguration failed with error 0x{ec:X}")
        raise NotImplementedError("Setting state is not implemented.")

    def _detect_available_configs() -> List[can.typechecking.AutoDetectedConfig]:
        nodeRange = CSI_NodeRange(CSI_NODE_MIN, CSI_NODE_MAX)
        tree = ctypes.POINTER(CSI_Tree)()
        ec = CSI_CreateProtocolTree(ctypes.c_char_p(b""), nodeRange, ctypes.byref(tree))
        if ec != 0x0:
            raise CanOperationError(
                f"CSI_CreateProtocolTree failed with error 0x{ec:X}"
            )

        nodes: Dict[str, str] = []

        def _findNodes(tree, prefix):
            uri = f"{prefix}/{tree.contents.item.uriName.decode()}"
            if "CAN:" in uri:
                nodes.append({"interface": "etas", "channel": uri})
            elif tree.contents.child:
                _findNodes(
                    tree.contents.child,
                    f"{prefix}/{tree.contents.item.uriName.decode()}",
                )

            if tree.contents.sibling:
                _findNodes(tree.contents.sibling, prefix)

        _findNodes(tree, "ETAS:/")

        ec = CSI_DestroyProtocolTree(tree)
        if ec != 0x0:
            raise CanOperationError(
                f"CSI_DestroyProtocolTree failed with error 0x{ec:X}"
            )

        return nodes

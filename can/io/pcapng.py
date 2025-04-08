"""
Contains handling of pcapng logging files.

pcapng file is a binary file format used for packet capture files.
Spec: https://www.ietf.org/archive/id/draft-tuexen-opsawg-pcapng-03.html
"""

import logging
from typing import Any, BinaryIO, Dict, Optional, Union

from ..message import Message
from ..socketcan_common import CAN_FRAME_HEADER_STRUCT_BE, build_can_frame
from ..typechecking import Channel, StringPathLike
from .generic import BinaryIOMessageWriter

logger = logging.getLogger("can.io.pcapng")

try:
    import pcapng
    from pcapng import blocks
except ImportError:
    pcapng = None


# https://www.tcpdump.org/linktypes.html
# https://www.tcpdump.org/linktypes/LINKTYPE_CAN_SOCKETCAN.html
LINKTYPE_CAN_SOCKETCAN = 227


class PcapngWriter(BinaryIOMessageWriter):
    """
    Logs CAN data to an pcapng file supported by Wireshark and other tools.
    """

    def __init__(
        self,
        file: Union[StringPathLike, BinaryIO],
        append: bool = False,
        tsresol: int = 9,
        **kwargs: Any,
    ) -> None:
        """
        :param file:
            A path-like object or as file-like object to write to.
            If this is a file-like object, is has to be opened in
            binary write mode, not text write mode.

        :param append:
            If True, the file will be opened in append mode. Otherwise,
            it will be opened in write mode. The default is False.

        :param tsresol:
            The time resolution of the timestamps in the pcapng file,
            expressed as -log10(unit in seconds),
            e.g. 9 for nanoseconds, 6 for microseconds.
            The default is 9, which corresponds to nanoseconds.
            .
        """
        if pcapng is None:
            raise NotImplementedError(
                "The python-pcapng package was not found. Install python-can with "
                "the optional dependency [pcapng] to use the PcapngWriter."
            )

        mode = "wb+"
        if append:
            mode = "ab+"

        # pcapng supports concatenation, and thus append
        super().__init__(file, mode=mode)
        self._header_block = blocks.SectionHeader(endianness=">")
        self._writer = pcapng.FileWriter(self.file, self._header_block)
        self._idbs: Dict[Channel, blocks.InterfaceDescription] = {}
        self.tsresol = tsresol

    def _resolve_idb(self, channel: Optional[Channel]) -> Any:
        channel_name = str(channel)
        if channel is None:
            channel_name = "can0"

        if channel_name not in self._idbs:
            idb = blocks.InterfaceDescription(
                section=self._header_block.section,
                link_type=LINKTYPE_CAN_SOCKETCAN,
                options={
                    "if_name": channel_name,
                    "if_tsresol": bytes([self.tsresol]),  # nanoseconds
                },
                endianness=">",  # big
            )
            self._header_block.register_interface(idb)
            self._writer.write_block(idb)
            self._idbs[channel_name] = idb

        return self._idbs[channel_name]

    def on_message_received(self, msg: Message) -> None:
        idb: blocks.InterfaceDescription = self._resolve_idb(msg.channel)
        timestamp_units = int(msg.timestamp * 10**self.tsresol)
        self._writer.write_block(
            blocks.EnhancedPacket(
                self._header_block.section,
                interface_id=idb.interface_id,
                packet_data=build_can_frame(msg, structure=CAN_FRAME_HEADER_STRUCT_BE),
                # timestamp (in tsresol units) = timestamp_high << 32 + timestamp_low
                timestamp_high=timestamp_units >> 32,
                timestamp_low=timestamp_units & 0xFFFFFFFF,
                endianness=">",  # big
            )
        )

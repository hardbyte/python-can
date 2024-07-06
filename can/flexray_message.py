"""
This module contains the implementation of :class:`can.FlexRayVFrReceiveMsgEx`.
"""

class FlexRayVFrReceiveMsgEx:
    """
    The :class:`~can.FlexRayVFrReceiveMsgEx` object is used to represent Flexray message.
    """

    __slots__ = [
        "timestamp", "is_flexray",
        "channel", "version", "channelMask", "_dir", "clientIndexFlexRayVFrReceiveMsgEx",
        "clusterNo", "frameId", "headerCrc1", "headerCrc2", "byteCount", "dataCount",
        "cycle", "tag", "_data", "frameFlags", "appParameter", "frameCrc", "frameLengthNs",
        "frameId1", "pduOffset", "blfLogMask", "reservedFlexRayVFrReceiveMsgEx1"
    ]

    def __init__(
        self, timestamp, is_flexray, channel, version, channelMask, _dir, 
        clientIndexFlexRayVFrReceiveMsgEx, clusterNo, frameId, headerCrc1, headerCrc2,
        byteCount, dataCount, cycle, tag, _data, frameFlags, appParameter, frameCrc,
        frameLengthNs, frameId1, pduOffset, blfLogMask, reservedFlexRayVFrReceiveMsgEx1
    ) -> None:
        """Create FlexRayVFrReceiveMsgEx object"""
        self.timestamp = timestamp
        self.is_flexray = is_flexray
        self.channel = channel
        self.version = version
        self.channelMask = channelMask
        self._dir = _dir
        self.clientIndexFlexRayVFrReceiveMsgEx = clientIndexFlexRayVFrReceiveMsgEx
        self.clusterNo = clusterNo
        self.frameId = frameId
        self.headerCrc1 = headerCrc1
        self.headerCrc2 = headerCrc2
        self.byteCount = byteCount
        self.dataCount = dataCount
        self.cycle = cycle
        self.tag = tag
        self._data = _data
        self.frameFlags = frameFlags
        self.appParameter = appParameter
        self.frameCrc = frameCrc
        self.frameLengthNs = frameLengthNs
        self.frameId1 = frameId1
        self.pduOffset = pduOffset
        self.blfLogMask = blfLogMask
        self.reservedFlexRayVFrReceiveMsgEx1 = reservedFlexRayVFrReceiveMsgEx1

# -*- coding: utf-8 -*-
"""
Ctypes wrapper module for Vector CAN Interface on win32/win64 systems
Authors: Julien Grave <grave.jul@gmail.com>, Christian Sandberg
"""
# Import Standard Python Modules
# ==============================
import ctypes
import logging
import sys
import time

# Import Modules
# ==============
from can import BusABC, Message
from .exceptions import VectorError

# Define Module Logger
# ====================
LOG = logging.getLogger(__name__)

# Import safely Vector API module for Travis tests
vxlapi = None
try:
    from . import vxlapi
except Exception as exc:
    LOG.warning('Could not import vxlapi: %s', exc)


class VectorBus(BusABC):
    """The CAN Bus implemented for the Vector interface."""

    def __init__(self, channel, can_filters=None, poll_interval=0.01,
                 bitrate=None, rx_queue_size=256, app_name="CANalyzer", **config):
        """
        :param list channel:
            The channel indexes to create this bus with.
            Can also be a single integer or a comma separated string.
        :param float poll_interval:
            Poll interval in seconds.
        :param int bitrate:
            Bitrate in bits/s.
        :param int rx_queue_size:
            Number of messages in receive queue.
        :param str app_name:
            Name of application in Hardware Config.
        """
        if vxlapi is None:
            raise ImportError("The Vector API has not been loaded")
        self.poll_interval = poll_interval
        if isinstance(channel, (list, tuple)):
            self.channels = channel
        elif isinstance(channel, int):
            self.channels = [channel]
        else:
            # Assume comma separated string of channels
            self.channels = [int(ch.strip()) for ch in channel.split(',')]
        self._app_name = app_name.encode()
        self.channel_info = 'Application %s: %s' % (
            app_name, ', '.join('CAN %d' % (ch + 1) for ch in self.channels))

        vxlapi.xlOpenDriver()
        self.port_handle = vxlapi.XLportHandle(vxlapi.XL_INVALID_PORTHANDLE)
        self.mask = 0
        # Get channels masks
        for channel in self.channels:
            hw_type = ctypes.c_uint(0)
            hw_index = ctypes.c_uint(0)
            hw_channel = ctypes.c_uint(0)
            vxlapi.xlGetApplConfig(self._app_name, channel, hw_type, hw_index,
                                   hw_channel, vxlapi.XL_BUS_TYPE_CAN)
            LOG.debug('Channel index %d found', channel)
            mask = vxlapi.xlGetChannelMask(hw_type.value, hw_index.value,
                                           hw_channel.value)
            LOG.debug('Channel %d, Type: %d, Mask: %d',
                      hw_channel.value, hw_type.value, mask)
            self.mask |= mask

        permission_mask = vxlapi.XLaccess()
        # Set mask to request channel init permission if needed
        if bitrate:
            permission_mask.value = self.mask
        vxlapi.xlOpenPort(self.port_handle, self._app_name, self.mask,
                          permission_mask, rx_queue_size,
                          vxlapi.XL_INTERFACE_VERSION, vxlapi.XL_BUS_TYPE_CAN)
        LOG.debug(
            'Open Port: PortHandle: %d, PermissionMask: 0x%X',
            self.port_handle.value, permission_mask.value)
        if bitrate:
            if permission_mask.value != self.mask:
                LOG.warning('Can not set bitrate since no init access')
            vxlapi.xlCanSetChannelBitrate(self.port_handle, permission_mask, bitrate)
        self.set_filters(can_filters)
        try:
            vxlapi.xlActivateChannel(self.port_handle, self.mask,
                                     vxlapi.XL_BUS_TYPE_CAN, 0)
        except VectorError:
            self.shutdown()
            raise
        # Calculate time offset for absolute timestamps
        offset = vxlapi.XLuint64()
        vxlapi.xlGetSyncTime(self.port_handle, offset)
        self._time_offset = time.time() - offset.value / 1000000000.0
        super(VectorBus, self).__init__()

    def set_filters(self, can_filters=None):
        if can_filters:
            # Only one filter per ID type allowed
            if len(can_filters) == 1 or (
                    len(can_filters) == 2 and
                    can_filters[0].get("extended") != can_filters[1].get("extended")):
                for can_filter in can_filters:
                    try:
                        vxlapi.xlCanSetChannelAcceptance(
                            self.port_handle, self.mask,
                            can_filter["can_id"], can_filter["can_mask"],
                            vxlapi.XL_CAN_EXT if can_filter.get("extended") else vxlapi.XL_CAN_STD)
                    except VectorError as exc:
                        LOG.warning("Could not set filters: %s", exc)
            else:
                LOG.warning("Only one filter per extended or standard ID allowed")

    def recv(self, timeout=None):
        end_time = time.time() + timeout if timeout is not None else None
        event = vxlapi.XLevent(0)
        while True:
            event_count = ctypes.c_uint(1)
            try:
                vxlapi.xlReceive(self.port_handle, event_count, event)
            except VectorError as exc:
                if exc.error_code != vxlapi.XL_ERR_QUEUE_IS_EMPTY:
                    raise
            else:
                if event.tag == vxlapi.XL_RECEIVE_MSG:
                    msg_id = event.tagData.msg.id
                    dlc = event.tagData.msg.dlc
                    flags = event.tagData.msg.flags
                    timestamp = event.timeStamp / 1000000000.0
                    msg = Message(
                        timestamp=timestamp + self._time_offset,
                        arbitration_id=msg_id & 0x1FFFFFFF,
                        extended_id=bool(msg_id & vxlapi.XL_CAN_EXT_MSG_ID),
                        is_remote_frame=bool(flags & vxlapi.XL_CAN_MSG_FLAG_REMOTE_FRAME),
                        is_error_frame=bool(flags & vxlapi.XL_CAN_MSG_FLAG_ERROR_FRAME),
                        dlc=dlc,
                        data=event.tagData.msg.data[:dlc],
                        channel=event.chanIndex)
                    return msg
            if end_time is not None and time.time() > end_time:
                return None
            time.sleep(self.poll_interval)

    def send(self, msg, timeout=None):
        message_count = ctypes.c_uint(1)
        msg_id = msg.arbitration_id
        if msg.id_type:
            msg_id |= vxlapi.XL_CAN_EXT_MSG_ID
        flags = 0
        if msg.is_remote_frame:
            flags |= vxlapi.XL_CAN_MSG_FLAG_REMOTE_FRAME
        xl_event = vxlapi.XLevent()
        xl_event.tag = vxlapi.XL_TRANSMIT_MSG
        xl_event.tagData.msg.id = msg_id
        xl_event.tagData.msg.dlc = msg.dlc
        xl_event.tagData.msg.flags = flags
        for idx, value in enumerate(msg.data):
            xl_event.tagData.msg.data[idx] = value
        vxlapi.xlCanTransmit(self.port_handle, self.mask, message_count, xl_event)

    def flush_tx_buffer(self):
        vxlapi.xlCanFlushTransmitQueue(self.port_handle, self.mask)

    def shutdown(self):
        vxlapi.xlDeactivateChannel(self.port_handle, self.mask)
        vxlapi.xlClosePort(self.port_handle)
        vxlapi.xlCloseDriver()
        
    def reset(self):
        vxlapi.xlDeactivateChannel(self.port_handle, self.mask)
        vxlapi.xlActivateChannel(self.port_handle, self.mask,
                                     vxlapi.XL_BUS_TYPE_CAN, 0)
   

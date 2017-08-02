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

# Define Module Logger
# ====================
LOG = logging.getLogger('can.vector')

# Import safely Vector API module for Travis tests
if sys.platform == 'win32':
    from . import vxlapi
else:
    LOG.warning('Vector API does not work on %s platform', sys.platform)
    vxlapi = None


class VectorBus(BusABC):
    """The CAN Bus implemented for the Vector interface."""

    def __init__(self, channel, can_filters=None, poll_interval=0.005,
                 app_name="CANalyzer", **config):
        """
        :param list channel:
            The channel indexes to create this bus with.
            Can also be a single integer or a comma separated string.
        :param float poll_interval:
            Poll interval in seconds.
        :param str app_name:
            Name of application in Hardware Config.
        """
        if vxlapi is None:
            raise ImportError("The Vector API has not been loaded")
        self.poll_interval = poll_interval
        if isinstance(channel, (list, tuple)):
            self.channel = channel
        elif isinstance(channel, int):
            self.channel = [channel]
        else:
            # Assume comma separated string of channels
            self.channel = [int(channel) for channel in channel.split(',')]
        self._app_name = app_name.encode()
        self._driver_init(can_filters)
        try:
            self._go_on_bus()
        except vxlapi.VectorError:
            self.shutdown()
            raise
        super(VectorBus, self).__init__()

    def _driver_init(self, can_filters):
        xl_status = vxlapi.open_driver()
        LOG.debug('Open Driver: Status: %d', xl_status.value)
        if xl_status.value == vxlapi.XL_SUCCESS:
            channel_mask = []
            # Get channels masks
            for channel in self.channel:
                app_channel = ctypes.c_uint(channel)
                hw_type = ctypes.c_uint(0)
                hw_index = ctypes.c_uint(0)
                hw_channel = ctypes.c_uint(0)
                xl_status = vxlapi.get_appl_config(
                    app_name=self._app_name,
                    app_channel=app_channel,
                    hw_type=hw_type,
                    hw_index=hw_index,
                    hw_channel=hw_channel)
                if xl_status.value == vxlapi.XL_SUCCESS:
                    LOG.debug('Channel index %d found', app_channel.value)
                    hw_type = ctypes.c_int(hw_type.value)
                    hw_index = ctypes.c_int(hw_index.value)
                    hw_channel = ctypes.c_int(hw_channel.value)
                    channel_mask.append(
                        vxlapi.get_channel_mask(hw_type, hw_index, hw_channel))
                    LOG.debug('Channel %d, Type: %d, Mask: %d',
                              hw_channel.value, hw_type.value,
                              channel_mask[app_channel.value].value)
            # Open one port for all channels
            self.mask = vxlapi.XLaccess(0)
            for CM in channel_mask:
                self.mask.value += CM.value
            self.port_handle = vxlapi.XLportHandle(
                vxlapi.XL_INVALID_PORTHANDLE)
            access_mask = self.mask
            permission_mask = self.mask
            xl_status = vxlapi.open_port(
                user_name=self._app_name,
                port_handle=self.port_handle,
                access_mask=access_mask,
                permission_mask=permission_mask)
            LOG.debug(
                'Open Port: PortHandle: %d, PermissionMask: %s, Status: %d',
                self.port_handle.value, permission_mask.value, xl_status.value)
            self.set_filters(can_filters)
        return xl_status

    def _go_on_bus(self):
        vxlapi.activate_channel(
            port_handle=self.port_handle, access_mask=self.mask)

    def set_filters(self, can_filters=None):
        if can_filters:
            # Only one filter per ID type allowed
            if len(can_filters) == 1 or (
                    len(can_filters) == 2 and
                    can_filters[0].get("extended") != can_filters[1].get("extended")):
                for can_filter in can_filters:
                    try:
                        vxlapi.can_set_channel_acceptance(
                            self.port_handle, self.mask,
                            can_filter["can_id"], can_filter["can_mask"],
                            vxlapi.XL_CAN_EXT if can_filter.get("extended") else vxlapi.XL_CAN_STD)
                    except vxlapi.VectorError as exc:
                        LOG.warning("Could not set filters: %s", exc)
            else:
                LOG.warning("Only one filter per extended or standard ID allowed")

    def recv(self, timeout=None):
        end_time = time.time() + timeout if timeout is not None else None
        event = vxlapi.XLevent(0)
        while True:
            event_count = ctypes.c_uint(1)
            try:
                vxlapi.receive(self.port_handle, event_count, event)
            except vxlapi.VectorError as exc:
                if exc.status != vxlapi.XL_ERR_QUEUE_IS_EMPTY:
                    raise
            if event.tag == vxlapi.XL_RECEIVE_MSG.value:
                msg_id = event.tagData.msg.id
                dlc = event.tagData.msg.dlc
                flags = event.tagData.msg.flags
                return Message(
                    timestamp=event.timeStamp / 1000000000.0,
                    arbitration_id=msg_id & 0x1FFFFFFF,
                    extended_id=bool(msg_id & vxlapi.XL_CAN_EXT_MSG_ID),
                    is_remote_frame=bool(flags & vxlapi.XL_CAN_MSG_FLAG_REMOTE_FRAME),
                    is_error_frame=bool(flags & vxlapi.XL_CAN_MSG_FLAG_ERROR_FRAME),
                    dlc=dlc,
                    data=event.tagData.msg.data[:dlc])
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
        xl_event.tag = vxlapi.XL_TRANSMIT_MSG.value
        xl_event.tagData.msg.id = msg_id
        xl_event.tagData.msg.dlc = msg.dlc
        xl_event.tagData.msg.flags = flags
        for idx, value in enumerate(msg.data):
            xl_event.tagData.msg.data[idx] = value
        xl_status = vxlapi.can_transmit(
            self.port_handle, self.mask, message_count, xl_event)

    def shutdown(self):
        vxlapi.deactivate_channel(self.port_handle, self.mask)
        vxlapi.close_port(self.port_handle)
        vxlapi.close_driver()

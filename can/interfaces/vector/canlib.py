# -*- coding: utf-8 -*-
"""
Ctypes wrapper module for Vector CAN Interface on win32/win64 systems
Authors: Julien Grave <grave.jul@gmail.com>
"""
# Import Standard Python Modules
# ==============================
import ctypes
import logging
import re
import sys

# Import Modules
# ==============
from can import BusABC, Message

# Define Module Logger
# ====================
LOG = logging.getLogger('can.vector')

# Import safely Vector API module for Travis tests
if sys.platform == 'win32':
    import vxlapi
else:
    LOG.warning('Vector API does not work on %s platform', sys.platform)
    vxlapi = None

# Define Module Constants
# =======================
RX_MSG_RE = re.compile(
    r'^RX_MSG c=(?P<channel>\d+), t=(?P<timestamp>\d+), (id=(?P<id>[\d\w]+) l=(?P<dlc>\d+)|type=(?P<type>\d+)),\s+(?P<data>[\d\w_]+)(?: (?P<flag>[\d\w]+))? tid=(?P<tid>\d+)$'
).match
CHIP_STATE_RE = re.compile(
    r'^CHIP_STATE c=(?P<channel>\d+), t=(?P<timestamp>\d+), busStatus=\s?(?P<busStatus>\w+), txErrCnt=(?P<txErrCnt>\d+), rxErrCnt=(?P<rxErrCnt>\d+)$'
).match


class VectorBus(BusABC):
    """The CAN Bus implemented for the Vector interface."""

    def __init__(self, channel, can_filters=None, **config):
        """
        :param list channel:
            The channel indexes to create this bus with.
        """
        if vxlapi is None:
            raise ImportError("The Vector API has not been loaded")
        if isinstance(channel, (list, tuple)):
            self.channel = channel
        else:
            raise ValueError('channel must be a list of integers')
        xl_status = self._driver_init()
        if xl_status.value == vxlapi.XL_SUCCESS:
            xl_status = self._go_on_bus()
        if xl_status.value != vxlapi.XL_SUCCESS:
            self.shutdown()
        super(VectorBus, self).__init__()

    def _driver_init(self):
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
                port_handle=self.port_handle,
                access_mask=access_mask,
                permission_mask=permission_mask)
            LOG.debug(
                'Open Port: PortHandle: %d, PermissionMask: %s, Status: %d',
                self.port_handle.value, permission_mask.value, xl_status.value)
        return xl_status

    def _go_on_bus(self):
        xl_status = vxlapi.activate_channel(
            port_handle=self.port_handle, access_mask=self.mask)
        return xl_status

    def recv(self, timeout=None):
        event_count = ctypes.c_uint(1)
        event_list = vxlapi.XLevent(0)
        xl_status = vxlapi.receive(self.port_handle, event_count, event_list)
        if xl_status.value != vxlapi.XL_ERR_QUEUE_IS_EMPTY:
            if xl_status.value != vxlapi.XL_SUCCESS:
                err_string = vxlapi.get_error_string(xl_status)
                LOG.debug(err_string.value)
            else:
                ev_string = vxlapi.get_event_string(event_list)
                if event_list.tag == vxlapi.XL_RECEIVE_MSG.value:
                    can_msg = RX_MSG_RE(ev_string.value)
                    if can_msg.group('id') is not None:
                        rx_msg = Message(
                            timestamp=long(can_msg.group('timestamp')),
                            arbitration_id=long(can_msg.group('id'), 16),
                            dlc=int(can_msg.group('dlc')),
                            data=can_msg.group('data'))
                        return rx_msg
                    elif can_msg.group('data') == 'ERROR_FRAME':
                        rx_msg = Message(
                            timestamp=long(can_msg.group('timestamp')),
                            is_error_frame=True,
                            arbitration_id=long(can_msg.group('type')))
                        return rx_msg
                    else:
                        return ev_string.value
                elif event_list.tag == vxlapi.XL_CHIP_STATE.value:
                    can_msg = CHIP_STATE_RE(ev_string.value)
                    return ev_string.value
                else:
                    return ev_string.value
        return None

    def send(self, msg):
        message_count = ctypes.c_uint(1)
        xl_event = vxlapi.XLevent()
        xl_event.tag = ctypes.c_ubyte(vxlapi.XL_TRANSMIT_MSG.value)
        xl_event.timeStamp = vxlapi.XLuint64(long(msg.timestamp))
        xl_event.tagData.msg.id = ctypes.c_ulong(msg.arbitration_id)
        xl_event.tagData.msg.dlc = ctypes.c_ushort(msg.dlc)
        xl_event.tagData.msg.flags = ctypes.c_ushort(0)
        for idx in range(0, msg.dlc):
            xl_event.tagData.msg.data[idx] = ctypes.c_ubyte(msg.data[idx])
        vxlapi.can_transmit(self.port_handle, self.mask, message_count,
                            xl_event)

    def shutdown(self):
        vxlapi.deactivate_channel(self.port_handle, self.mask)
        vxlapi.close_port(self.port_handle)
        vxlapi.close_driver()

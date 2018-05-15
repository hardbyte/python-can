#!/usr/bin/env python
# coding: utf-8

"""
ICS NeoVi interface module.

python-ics is a Python wrapper around the API provided by Intrepid Control 
Systems for communicating with their NeoVI range of devices.

Implementation references:
* https://github.com/intrepidcs/python_ics
"""

import logging
from collections import deque

from can import Message, CanError, BusABC

logger = logging.getLogger(__name__)

try:
    import ics
except ImportError as ie:
    logger.warning(
        "You won't be able to use the ICS NeoVi can backend without the "
        "python-ics module installed!: %s", ie
    )
    ics = None


class ICSApiError(CanError):
    """
    TODO add docs
    """

    # A critical error which affects operation or accuracy.
    ICS_SPY_ERR_CRITICAL = 0x10
    # An error which is not understood.
    ICS_SPY_ERR_QUESTION = 0x20
    # An important error which may be critical depending on the application
    ICS_SPY_ERR_EXCLAMATION = 0x30
    # An error which probably does not need attention.
    ICS_SPY_ERR_INFORMATION = 0x40

    def __init__(
            self, error_number, description_short, description_long,
            severity, restart_needed
    ):
        super(ICSApiError, self).__init__(description_short)
        self.error_number = error_number
        self.description_short = description_short
        self.description_long = description_long
        self.severity = severity
        self.restart_needed = restart_needed == 1

    def __str__(self):
        return "{} {}".format(self.description_short, self.description_long)

    @property
    def is_critical(self):
        return self.severity == self.ICS_SPY_ERR_CRITICAL


BAUDRATE_SETTING = {
    20000: 0,
    33333: 1,
    50000: 2,
    62500: 3,
    83333: 4,
    100000: 5,
    125000: 6,
    250000: 7,
    500000: 8,
    800000: 9,
    1000000: 10,
}
VALID_BITRATES = list(BAUDRATE_SETTING.keys())
VALID_BITRATES.sort()


class NeoViBus(BusABC):
    """
    The CAN Bus implemented for the python_ics interface
    https://github.com/intrepidcs/python_ics
    """

    def __init__(self, channel=None, can_filters=None, **config):
        """
        :param int channel:
            The Channel id to create this bus with.
        :param list can_filters:
            See :meth:`can.BusABC.set_filters` for details.

        :param use_system_timestamp:
            Use system timestamp for can messages instead of the hardware time
            stamp
        :param str serial:
            Serial to connect (optional, will use the first found if not
            supplied)
        :param int bitrate:
            Channel bitrate in bit/s. (optional, will enable the auto bitrate
            feature if not supplied)
        """
        if ics is None:
            raise ImportError('Please install python-ics')

        super(NeoViBus, self).__init__(channel=channel, can_filters=can_filters, **config)

        logger.info("CAN Filters: {}".format(can_filters))
        logger.info("Got configuration of: {}".format(config))

        self._use_system_timestamp = bool(config.get('use_system_timestamp', False))

        # TODO: Add support for multiple channels
        try:
            channel = int(channel)
        except ValueError:
            raise ValueError('channel must be an integer')

        type_filter = config.get('type_filter')
        serial = config.get('serial')
        self.dev = self._find_device(type_filter, serial)
        ics.open_device(self.dev)

        bitrate = config.get('bitrate')

        # Default auto baud setting
        settings = {
            'SetBaudrate': ics.AUTO,
            'Baudrate': BAUDRATE_SETTING[500000],   # Default baudrate setting
            'auto_baud': 1
        }

        if bitrate is not None:
            bitrate = int(bitrate)
            if bitrate not in VALID_BITRATES:
                raise ValueError(
                    'Invalid bitrate. Valid bitrates are {}'.format(
                        VALID_BITRATES
                    )
                )
            baud_rate_setting = BAUDRATE_SETTING[bitrate]
            settings = {
                'SetBaudrate': ics.AUTO,
                'Baudrate': baud_rate_setting,
                'auto_baud': 0,
            }
        self._set_can_settings(channel, settings)

        self.channel_info = '%s %s CH:%s' % (
            self.dev.Name,
            self.get_serial_number(self.dev),
            channel
        )
        logger.info("Using device: {}".format(self.channel_info))

        self.rx_buffer = deque()
        self.opened = True

        self.network = channel if channel is not None else None

        # TODO: Change the scaling based on the device type
        self.ts_scaling = (
            ics.NEOVI6_VCAN_TIMESTAMP_1, ics.NEOVI6_VCAN_TIMESTAMP_2
        )

    @staticmethod
    def get_serial_number(device):
        """Decode (if needed) and return the ICS device serial string

        :param device: ics device
        :return: ics device serial string
        :rtype: str
        """
        a0000 = 604661760
        if device.SerialNumber >= a0000:
            return ics.base36enc(device.SerialNumber)
        return str(device.SerialNumber)

    def shutdown(self):
        super(NeoViBus, self).shutdown()
        self.opened = False
        ics.close_device(self.dev)

    def _find_device(self, type_filter=None, serial=None):
        if type_filter is not None:
            devices = ics.find_devices(type_filter)
        else:
            devices = ics.find_devices()

        for device in devices:
            if serial is None or self.get_serial_number(device) == str(serial):
                dev = device
                break
        else:
            msg = ['No device']

            if type_filter is not None:
                msg.append('with type {}'.format(type_filter))
            if serial is not None:
                msg.append('with serial {}'.format(serial))
            msg.append('found.')
            raise Exception(' '.join(msg))
        return dev

    def _get_can_settings(self, channel):
        """Return the CanSettings for channel

        :param channel: can channel number
        :return: ics.CanSettings
        """
        device_settings = ics.get_device_settings(self.dev)
        return getattr(device_settings, 'can{}'.format(channel))

    def _set_can_settings(self, channel, setting):
        """Applies can settings to channel

        :param channel: can channel number
        :param setting: settings dictionary (only the settings to update)
        :return: None
        """
        device_settings = ics.get_device_settings(self.dev)
        channel_settings = getattr(device_settings, 'can{}'.format(channel))
        for setting, value in setting.items():
            setattr(channel_settings, setting, value)
        ics.set_device_settings(self.dev, device_settings)

    def _process_msg_queue(self, timeout):
        try:
            messages, errors = ics.get_messages(self.dev, False, timeout)
        except ics.RuntimeError:
            return
        for ics_msg in messages:
            if ics_msg.NetworkID != self.network:
                continue
            self.rx_buffer.append(ics_msg)
        if errors:
            logger.warning("%d error(s) found" % errors)

            for msg in ics.get_error_messages(self.dev):
                error = ICSApiError(*msg)
                if error.is_critical:
                    raise error
                logger.warning(error)

    def _get_timestamp_for_msg(self, ics_msg):
        if self._use_system_timestamp:
            # This is the system time stamp.
            # TimeSystem is loaded with the value received from the timeGetTime
            # call in the WIN32 multimedia API.
            #
            # The timeGetTime accuracy is up to 1 millisecond. See the WIN32
            # API documentation for more information.
            #
            # This timestamp is useful for time comparing with other system
            # events or data which is not synced with the neoVI timestamp.
            #
            # Currently, TimeSystem2 is not used.
            return ics_msg.TimeSystem
        else:
            # This is the hardware time stamp.
            # The TimeStamp is reset to zero every time the OpenPort method is
            # called.
            return \
                float(ics_msg.TimeHardware2) * self.ts_scaling[1] + \
                float(ics_msg.TimeHardware) * self.ts_scaling[0]

    def _ics_msg_to_message(self, ics_msg):
        return Message(
            timestamp=self._get_timestamp_for_msg(ics_msg),
            arbitration_id=ics_msg.ArbIDOrHeader,
            data=ics_msg.Data[:ics_msg.NumberBytesData],
            dlc=ics_msg.NumberBytesData,
            extended_id=bool(
                ics_msg.StatusBitField & ics.SPY_STATUS_XTD_FRAME
            ),
            is_remote_frame=bool(
                ics_msg.StatusBitField & ics.SPY_STATUS_REMOTE_FRAME
            ),
            channel=ics_msg.NetworkID
        )

    def _recv_internal(self, timeout):
        if not self.rx_buffer:
            self._process_msg_queue(timeout)

        try:
            ics_msg = self.rx_buffer.popleft()
            msg = self._ics_msg_to_message(ics_msg)
        except IndexError:
            return None, False
        else:
            return msg, False

    def send(self, msg, timeout=None):
        if not self.opened:
            raise CanError("bus not yet opened")

        flags = 0
        if msg.is_extended_id:
            flags |= ics.SPY_STATUS_XTD_FRAME
        if msg.is_remote_frame:
            flags |= ics.SPY_STATUS_REMOTE_FRAME

        message = ics.SpyMessage()
        message.ArbIDOrHeader = msg.arbitration_id
        message.NumberBytesData = len(msg.data)
        message.Data = tuple(msg.data)
        message.StatusBitField = flags
        message.StatusBitField2 = 0
        message.NetworkID = self.network

        try:
            ics.transmit_messages(self.dev, message)
        except ics.RuntimeError:
            raise ICSApiError(*ics.get_last_api_error(self.dev))

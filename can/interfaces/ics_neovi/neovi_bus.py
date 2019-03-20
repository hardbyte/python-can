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
    Indicates an error with the ICS API.
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


class NeoViBus(BusABC):
    """
    The CAN Bus implemented for the python_ics interface
    https://github.com/intrepidcs/python_ics
    """

    def __init__(self, channel, can_filters=None, **kwargs):
        """
        :param channel:
            The channel ids to create this bus with.
            Can also be a single integer, netid name or a comma separated
            string.
        :type channel: int or str or list(int) or list(str)
        :param list can_filters:
            See :meth:`can.BusABC.set_filters` for details.
        :param bool receive_own_messages:
            If transmitted messages should also be received by this bus.
        :param bool use_system_timestamp:
            Use system timestamp for can messages instead of the hardware time
            stamp
        :param str serial:
            Serial to connect (optional, will use the first found if not
            supplied)
        :param int bitrate:
            Channel bitrate in bit/s. (optional, will enable the auto bitrate
            feature if not supplied)
        :param bool fd:
            If CAN-FD frames should be supported.
        :param int data_bitrate:
            Which bitrate to use for data phase in CAN FD.
            Defaults to arbitration bitrate.
        :param override_library_name:
            Absolute path or relative path to the library including filename.
        """
        if ics is None:
            raise ImportError('Please install python-ics')

        super(NeoViBus, self).__init__(
            channel=channel, can_filters=can_filters, **kwargs)

        logger.info("CAN Filters: {}".format(can_filters))
        logger.info("Got configuration of: {}".format(kwargs))

        if 'override_library_name' in kwargs:
            ics.override_library_name(kwargs.get('override_library_name'))

        if isinstance(channel, (list, tuple)):
            self.channels = channel
        elif isinstance(channel, int):
            self.channels = [channel]
        else:
            # Assume comma separated string of channels
            self.channels = [ch.strip() for ch in channel.split(',')]
        self.channels = [NeoViBus.channel_to_netid(ch) for ch in self.channels]

        type_filter = kwargs.get('type_filter')
        serial = kwargs.get('serial')
        self.dev = self._find_device(type_filter, serial)
        ics.open_device(self.dev)

        if 'bitrate' in kwargs:
            for channel in self.channels:
                ics.set_bit_rate(self.dev, kwargs.get('bitrate'), channel)

        fd = kwargs.get('fd', False)
        if fd:
            if 'data_bitrate' in kwargs:
                for channel in self.channels:
                    ics.set_fd_bit_rate(
                        self.dev, kwargs.get('data_bitrate'), channel)

        self._use_system_timestamp = bool(
            kwargs.get('use_system_timestamp', False)
        )
        self._receive_own_messages = kwargs.get('receive_own_messages', True)

        self.channel_info = '%s %s CH:%s' % (
            self.dev.Name,
            self.get_serial_number(self.dev),
            self.channels
        )
        logger.info("Using device: {}".format(self.channel_info))

        self.rx_buffer = deque()

    @staticmethod
    def channel_to_netid(channel_name_or_id):
        try:
            channel = int(channel_name_or_id)
        except ValueError:
            netid = "NETID_{}".format(channel_name_or_id.upper())
            if hasattr(ics, netid):
                channel = getattr(ics, netid)
            else:
                raise ValueError(
                    'channel must be an integer or '
                    'a valid ICS channel name'
                )
        return channel

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
        ics.close_device(self.dev)

    @staticmethod
    def _detect_available_configs():
        """Detect all configurations/channels that this interface could
        currently connect with.

        :rtype: Iterator[dict]
        :return: an iterable of dicts, each being a configuration suitable
                 for usage in the interface's bus constructor.
        """
        if ics is None:
            return []

        try:
            devices = ics.find_devices()
        except Exception as e:
            logger.debug("Failed to detect configs: %s", e)
            return []

        # TODO: add the channel(s)
        return [{
            'interface': 'neovi',
            'serial': NeoViBus.get_serial_number(device)
        } for device in devices]

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

    def _process_msg_queue(self, timeout=0.1):
        try:
            messages, errors = ics.get_messages(self.dev, False, timeout)
        except ics.RuntimeError:
            return
        for ics_msg in messages:
            if ics_msg.NetworkID not in self.channels:
                continue
            is_tx = bool(ics_msg.StatusBitField & ics.SPY_STATUS_TX_MSG)
            if not self._receive_own_messages and is_tx:
                continue
            self.rx_buffer.append(ics_msg)
        if errors:
            logger.warning("%d error(s) found" % errors)

            for msg in ics.get_error_messages(self.dev):
                error = ICSApiError(*msg)
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
            return ics.get_timestamp_for_msg(self.dev, ics_msg)

    def _ics_msg_to_message(self, ics_msg):
        is_fd = ics_msg.Protocol == ics.SPY_PROTOCOL_CANFD

        if is_fd:
            if ics_msg.ExtraDataPtrEnabled:
                data = ics_msg.ExtraDataPtr[:ics_msg.NumberBytesData]
            else:
                data = ics_msg.Data[:ics_msg.NumberBytesData]

            return Message(
                timestamp=self._get_timestamp_for_msg(ics_msg),
                arbitration_id=ics_msg.ArbIDOrHeader,
                data=data,
                dlc=ics_msg.NumberBytesData,
                is_extended_id=bool(
                    ics_msg.StatusBitField & ics.SPY_STATUS_XTD_FRAME
                ),
                is_fd=is_fd,
                is_remote_frame=bool(
                    ics_msg.StatusBitField & ics.SPY_STATUS_REMOTE_FRAME
                ),
                error_state_indicator=bool(
                    ics_msg.StatusBitField3 & ics.SPY_STATUS3_CANFD_ESI
                ),
                bitrate_switch=bool(
                    ics_msg.StatusBitField3 & ics.SPY_STATUS3_CANFD_BRS
                ),
                channel=ics_msg.NetworkID
            )
        else:
            return Message(
                timestamp=self._get_timestamp_for_msg(ics_msg),
                arbitration_id=ics_msg.ArbIDOrHeader,
                data=ics_msg.Data[:ics_msg.NumberBytesData],
                dlc=ics_msg.NumberBytesData,
                is_extended_id=bool(
                    ics_msg.StatusBitField & ics.SPY_STATUS_XTD_FRAME
                ),
                is_fd=is_fd,
                is_remote_frame=bool(
                    ics_msg.StatusBitField & ics.SPY_STATUS_REMOTE_FRAME
                ),
                channel=ics_msg.NetworkID
            )

    def _recv_internal(self, timeout=0.1):
        if not self.rx_buffer:
            self._process_msg_queue(timeout=timeout)
        try:
            ics_msg = self.rx_buffer.popleft()
            msg = self._ics_msg_to_message(ics_msg)
        except IndexError:
            return None, False
        return msg, False

    def send(self, msg, timeout=None):
        if not ics.validate_hobject(self.dev):
            raise CanError("bus not open")
        message = ics.SpyMessage()

        flag0 = 0
        if msg.is_extended_id:
            flag0 |= ics.SPY_STATUS_XTD_FRAME
        if msg.is_remote_frame:
            flag0 |= ics.SPY_STATUS_REMOTE_FRAME

        flag3 = 0
        if msg.is_fd:
            message.Protocol = ics.SPY_PROTOCOL_CANFD
            if msg.bitrate_switch:
                flag3 |= ics.SPY_STATUS3_CANFD_BRS
            if msg.error_state_indicator:
                flag3 |= ics.SPY_STATUS3_CANFD_ESI

        message.ArbIDOrHeader = msg.arbitration_id
        message.NumberBytesData = len(msg.data)
        message.Data = tuple(msg.data[:8])
        if msg.is_fd and len(msg.data) > 8:
            message.ExtraDataPtrEnabled = 1
            message.ExtraDataPtr = tuple(msg.data)
        message.StatusBitField = flag0
        message.StatusBitField2 = 0
        message.StatusBitField3 = flag3
        if msg.channel is not None:
            message.NetworkID = msg.channel
        elif len(self.channels) == 1:
            message.NetworkID = self.channels[0]
        else:
            raise ValueError(
                "msg.channel must be set when using multiple channels.")

        try:
            ics.transmit_messages(self.dev, message)
        except ics.RuntimeError:
            raise ICSApiError(*ics.get_last_api_error(self.dev))

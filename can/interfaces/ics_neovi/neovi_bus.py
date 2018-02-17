"""
ICS NeoVi interface module.

python-ics is a Python wrapper around the API provided by Intrepid Control 
Systems for communicating with their NeoVI range of devices.

Implementation references:
* https://github.com/intrepidcs/python_ics
"""

import logging
from collections import deque

from can import Message, CanError
from can.bus import BusABC

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

    def __init__(self, channel=None, can_filters=None, **config):
        """

        :param int channel:
            The Channel id to create this bus with.
        :param list can_filters:
            A list of dictionaries each containing a "can_id" and a "can_mask".
        :param use_system_timestamp:
            Use system timestamp for can messages instead of the hardware time
            stamp

                >>> [{"can_id": 0x11, "can_mask": 0x21}]

        """
        super(NeoViBus, self).__init__(channel, can_filters, **config)
        if ics is None:
            raise ImportError('Please install python-ics')

        logger.info("CAN Filters: {}".format(can_filters))
        logger.info("Got configuration of: {}".format(config))

        self._use_system_timestamp = bool(
            config.get('use_system_timestamp', False)
        )

        # TODO: Add support for multiples channels
        try:
            channel = int(channel)
        except ValueError:
            raise ValueError('channel must be an integer')

        type_filter = config.get('type_filter')
        serial = config.get('serial')
        self.dev = self._open_device(type_filter, serial)

        self.channel_info = '%s %s CH:%s' % (
            self.dev.Name,
            self.get_serial_number(self.dev),
            channel
        )
        logger.info("Using device: {}".format(self.channel_info))

        ics.load_default_settings(self.dev)

        self.sw_filters = None
        self.set_filters(can_filters)
        self.rx_buffer = deque()
        self.opened = True

        self.network = int(channel) if channel is not None else None

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
        def to_base36(n, alphabet="0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
            return (to_base36(n // 36) + alphabet[n % 36]).lstrip("0") \
                if n > 0 else "0"

        a0000 = 604661760
        if device.SerialNumber >= a0000:
            return to_base36(device.SerialNumber)
        return str(device.SerialNumber)

    def shutdown(self):
        super(NeoViBus, self).shutdown()
        self.opened = False
        ics.close_device(self.dev)

    def _open_device(self, type_filter=None, serial=None):
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
        ics.open_device(dev)
        return dev

    def _process_msg_queue(self, timeout=None):
        try:
            messages, errors = ics.get_messages(self.dev, False, timeout)
        except ics.RuntimeError:
            return
        for ics_msg in messages:
            if ics_msg.NetworkID != self.network:
                continue
            if not self._is_filter_match(ics_msg.ArbIDOrHeader):
                continue
            self.rx_buffer.append(ics_msg)
        if errors:
            logger.warning("%d error(s) found" % errors)

            for msg in ics.get_error_messages(self.dev):
                error = ICSApiError(*msg)
                if error.is_critical:
                    raise error
                logger.warning(error)

    def _is_filter_match(self, arb_id):
        """
        If SW filtering is used, checks if the `arb_id` matches any of
        the filters setup.

        :param int arb_id:
            CAN ID to check against.

        :return:
            True if `arb_id` matches any filters
            (or if SW filtering is not used).
        """
        if not self.sw_filters:
            # Filtering done on HW or driver level or no filtering
            return True
        for can_filter in self.sw_filters:
            if not (arb_id ^ can_filter['can_id']) & can_filter['can_mask']:
                return True
        return False

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

    def recv(self, timeout=None):
        msg = None
        if not self.rx_buffer:
            self._process_msg_queue(timeout=timeout)

        try:
            ics_msg = self.rx_buffer.popleft()
            msg = self._ics_msg_to_message(ics_msg)
        except IndexError:
            pass
        return msg

    def send(self, msg, timeout=None):
        if not self.opened:
            return
        data = tuple(msg.data)

        flags = 0
        if msg.is_extended_id:
            flags |= ics.SPY_STATUS_XTD_FRAME
        if msg.is_remote_frame:
            flags |= ics.SPY_STATUS_REMOTE_FRAME

        message = ics.SpyMessage()
        message.ArbIDOrHeader = msg.arbitration_id
        message.NumberBytesData = len(data)
        message.Data = data
        message.StatusBitField = flags
        message.StatusBitField2 = 0
        message.NetworkID = self.network

        try:
            ics.transmit_messages(self.dev, message)
        except ics.RuntimeError:
            raise ICSApiError(*ics.get_last_api_error(self.dev))

    def set_filters(self, can_filters=None):
        """Apply filtering to all messages received by this Bus.

        Calling without passing any filters will reset the applied filters.

        :param list can_filters:
            A list of dictionaries each containing a "can_id" and a "can_mask".

            >>> [{"can_id": 0x11, "can_mask": 0x21}]

            A filter matches, when
            ``<received_can_id> & can_mask == can_id & can_mask``

        """
        self.sw_filters = can_filters or []

        if not len(self.sw_filters):
            logger.info("Filtering has been disabled")
        else:
            for can_filter in can_filters:
                can_id = can_filter["can_id"]
                can_mask = can_filter["can_mask"]
                logger.info(
                    "Filtering on ID 0x%X, mask 0x%X", can_id, can_mask)

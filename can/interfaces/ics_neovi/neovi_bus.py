"""
ICS NeoVi interface module.

python-ics is a Python wrapper around the API provided by Intrepid Control 
Systems for communicating with their NeoVI range of devices.

Implementation references:
* https://github.com/intrepidcs/python_ics
"""

import logging

try:
    import queue
except ImportError:
    import Queue as queue

from can import Message
from can.bus import BusABC

logger = logging.getLogger(__name__)

try:
    import ics
except ImportError:
    logger.error(
        "You won't be able to use the ICS NeoVi can backend without the "
        "python-ics module installed!"
    )
    ics = None


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
            raise Exception('Please install python-ics')

        logger.info("CAN Filters: {}".format(can_filters))
        logger.info("Got configuration of: {}".format(config))

        self._use_system_timestamp = bool(
            config.get('use_system_timestamp', False)
        )

        try:
            channel = int(channel)
        except ValueError:
            raise ValueError('channel must be an integer')

        type_filter = config.get('type_filter')
        serial = config.get('serial')
        self.dev = self._open_device(type_filter, serial)

        self.channel_info = '%s %s CH:%s' % (
            self.dev.Name,
            self.dev.SerialNumber,
            channel
        )
        logger.info("Using device: {}".format(self.channel_info))

        ics.load_default_settings(self.dev)

        self.sw_filters = None
        self.set_filters(can_filters)
        self.rx_buffer = queue.Queue()
        self.opened = True

        self.network = int(channel) if channel is not None else None

        # TODO: Change the scaling based on the device type
        self.ts_scaling = (
            ics.NEOVI6_VCAN_TIMESTAMP_1, ics.NEOVI6_VCAN_TIMESTAMP_2
        )

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
            if serial is None:
                dev = device
                break
            if str(device.SerialNumber) == serial:
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
            if ics_msg.ArbIDOrHeader == 0:
                # Looks like ICS device sends frames with ArbIDOrHeader = 0
                # Need to find out exactly what they are for
                # Filtering them for now
                continue
            if not self._is_filter_match(ics_msg.ArbIDOrHeader):
                continue
            self.rx_buffer.put(ics_msg)
        if errors:
            logger.warning("%d errors found" % errors)

            for msg in ics.get_error_messages(self.dev):
                logger.warning(msg)

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
            )
        )

    def recv(self, timeout=None):
        try:
            self._process_msg_queue(timeout=timeout)
            ics_msg = self.rx_buffer.get_nowait()
            self.rx_buffer.task_done()
            return self._ics_msg_to_message(ics_msg)
        except queue.Empty:
            pass
        return None

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
        ics.transmit_messages(self.dev, message)

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

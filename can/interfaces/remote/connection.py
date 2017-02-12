import struct
from can.interfaces.remote import events


class EventTypes(object):
    """Keeps track of event classes that are supported."""

    def __init__(self):
        self._event_classes = {}

    def register(self, event_cls):
        if event_cls.EVENT_ID in self._event_classes:
            raise ProtocolError('Duplicate event type registered')
        self._event_classes[event_cls.EVENT_ID] = event_cls

    def __getitem__(self, event_id):
        return self._event_classes[event_id]


class Connection(object):
    """A connection handles buffering of raw data received from e.g. a socket
    and converts the data stream to a stream of events.

    Received events can be iterated over using this class.
    """

    def __init__(self):
        self._send_buf = bytearray()
        self._recv_buf = bytearray()
        #: Indicates if the sender has closed the connection
        self.closed = False

    def receive_data(self, buf):
        """Feed data received from source.

        :param buf:
            A bytes-like object. If empty, the connection is considered closed.
        """
        if not buf:
            self.closed = True
        self._recv_buf += buf

    def send_event(self, event):
        """Convert event to data that can be transmitted as bytes.

        :param event:
            Event to be sent
        """
        data = struct.pack('B', event.EVENT_ID) + event.encode()
        self._send_buf += data

    def next_data(self):
        """Get next set of data to be transmitted.

        The internal send buffer will be cleared.

        :return:
            A bytes-like object.
        """
        data = self._send_buf
        self._send_buf = bytearray()
        return data

    def next_event(self):
        """Get next event, if any.

        :return:
            An event object or None if not enough data exists.
        """
        if not self._recv_buf:
            if self.closed:
                return events.ConnectionClosed()
            return None

        event_id = self._recv_buf[0]
        try:
            Event = event_types[event_id]
        except KeyError:
            raise ProtocolError('%d is not a valid event ID' % event_id)
        try:
            event = Event.from_buffer(self._recv_buf[1:])
        except events.NeedMoreDataError:
            return None

        # Remove processed data from buffer
        del self._recv_buf[:1+len(event)]
        return event

    def data_ready(self):
        """Check if there is data to transmit.

        :rtype: bool
        """
        return len(self._send_buf) > 0

    def __iter__(self):
        """Allow iteration on events in the buffer.

            >>> for event in conn:
            ...     print(event)

        :yields: Event objects.
        """
        while True:
            event = self.next_event()
            if event is None:
                break
            yield event


class ProtocolError(Exception):
    pass


event_types = EventTypes()
event_types.register(events.BusRequest)
event_types.register(events.BusResponse)
event_types.register(events.CanMessage)
event_types.register(events.TransmitSuccess)
event_types.register(events.TransmitFail)
event_types.register(events.RemoteException)
event_types.register(events.PeriodicMessageStart)
event_types.register(events.PeriodicMessageStop)
event_types.register(events.FilterConfig)
event_types.register(events.ConnectionClosed)

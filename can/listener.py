try:
    import queue
except ImportError:
    import Queue as queue


class Listener(object):

    def on_message_received(self, msg):
        raise NotImplementedError(
            "{} has not implemented on_message_received".format(
                self.__class__.__name__)
        )

    def __call__(self, msg):
        return self.on_message_received(msg)

    def stop(self):
        """
        Override to cleanup any open resources.
        """


class RedirectReader(Listener):
    """
    A RedirectReader sends all received messages
    to another Bus.

    """

    def __init__(self, bus):
        self.bus = bus

    def on_message_received(self, msg):
        self.bus.send(msg)


class BufferedReader(Listener):
    """
    A BufferedReader is a subclass of :class:`~can.Listener` which implements a
    **message buffer**: that is, when the :class:`can.BufferedReader` instance is
    notified of a new message it pushes it into a queue of messages waiting to
    be serviced.
    """

    def __init__(self):
        self.buffer = queue.Queue(0)

    def on_message_received(self, msg):
        self.buffer.put(msg)

    def get_message(self, timeout=0.5):
        """
        Attempts to retrieve the latest message received by the instance. If no message is
        available it blocks for given timeout or until a message is received (whichever
        is shorter),

        :param float timeout: The number of seconds to wait for a new message.
        :return: the :class:`~can.Message` if there is one, or None if there is not.
        """
        try:
            return self.buffer.get(block=True, timeout=timeout)
        except queue.Empty:
            return None

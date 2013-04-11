# -*- coding: utf-8 -*-

import abc
import threading
import time
import logging
logger = logging.getLogger(__name__)
try:
    import queue
except ImportError:
    import Queue as queue


class BusABC(object):
    """CAN Bus Abstract Base Class

    External API:

        * write(message)
            Transmit message to CAN bus.

        * channel_info
            str attribute describing underlying bus

        * listeners
            list of callables to process received messages

    Concrete implementations must implement the following methods:
        * _get_message
        * _put_message
        
    As well as setting the `channel_info` attribute to a string describing the
    interface.
    
    """
    
    # a string describing the channel
    channel_info = 'unknown'
       
    def __init__(self, *args, **kwargs):
        # list of callback functions which will be passed Message instances.
        self.listeners = []
        
        # buffer for messages to be written to the bus
        self._tx_queue = queue.Queue()
        
        self._running = threading.Event()
        self._running.set()
        
        self._read_thread = threading.Thread(target=self.rx_thread)
        self._read_thread.daemon = True

        self._read_thread.start()
    

    @abc.abstractmethod
    def _get_message(self, timeout=None):
        """Block waiting for a message from the Bus.  
        
        :return:
            None on timeout or a :class:`can.Message` object.
        """
        raise NotImplementedError("Trying to read from a write only bus?")

    @abc.abstractmethod
    def _put_message(self, msg):
        """Override this method to enable the transmit path.

        :param :class:`can.Message` msg:

        :raise :class:`can.CanError`:
            if the message could not be written.
        """
        raise NotImplementedError("Trying to write to a readonly bus?")

    def __iter__(self):
        """Allow iteration on messages as they are received.

            >>> for msg in bus:
            ...     print(msg)


        :yields: :class:`can.Message` msg objects.
        """
        while True:
            yield self._get_message()
        logger.debug("done iterating over bus messages")

    def write(self, msg):
        """
        :param :class:`can.Message` msg:
            A Message object to write to bus.
        """
        self._put_message(msg)
        logger.debug("Message added to transmit queue")

    def rx_thread(self):
        """
        The consumer thread.
        """
        while self._running.is_set():
            rx_msg = self._get_message()
            
            if rx_msg is not None:
                for callback in self.listeners:
                    callback(rx_msg)

    def write_for_period(self, interval, total_time, message, block=True):
        """This method should be overridden by CAN interfaces
        which can set up periodic message sending tasks.
        
        :param float interval:
            Interval in seconds between sending messages.
        
        :param float total_time:
            Time in seconds to keep sending this message for.
            
        :param :class:`can.Message` message:
            The message to send periodically.
        """
        def periodic_sender():
            start_time = time.time()
            while (time.time() - start_time) < total_time:
                self.write(message)
                time.sleep(interval)
        if block:
            return periodic_sender()
        else:
            t = threading.Thread(target=periodic_sender)
            t.start()

    def flush_tx_buffer(self):
        pass

    def shutdown(self):
        self.flush_tx_buffer()
        self._running.clear()


    __metaclass__ = abc.ABCMeta

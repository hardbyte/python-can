# -*- coding: utf-8 -*-

import abc
import threading
try:
    import queue
except ImportError:
    import Queue as queue


class BusABC(object):
    """CAN Bus Abstract Base Class

    Concrete implementations must implement the following methods:
        * _get_message
        * _put_message
        
    As well as setting the channel_info attribute to a string describing the
    interface.
    
    """
    
    # a string describing the channel
    channel_info = 'unknown'    
       
    def __init__(self, *args, **kwargs):
        # list of callback functions which will be passed Message instances.
        self.listeners = []
        
        # buffer for messages to be written to the bus
        self._tx_queue = queue.Queue()
        
        self._threads_running = threading.Event()
        self._threads_running.set()
        
        self._write_thread = threading.Thread(target=self.tx_thread)
        self._write_thread.daemon = True
        self._write_thread.start()
        
        self._read_thread = threading.Thread(target=self.rx_thread)
        self._read_thread.daemon = True
        self._read_thread.start()
    

    @abc.abstractmethod
    def _get_message(self, timeout=None):
        """Block waiting for a message from the Bus.  
        
        :return:
            None on timeout or a :class:`can.Message` object.
        """
    
    
    @abc.abstractmethod
    def _put_message(self, msg):
        """Override this method to enable the transmit path.
        
        :param :class:`can.Message` msg:
        
        :raise :class:`can.CanError`:
            if the message could not be written.
        """
    
    
    def write(self, msg):
        ''''
        :param :class:`can.Message` msg:
            A Message object to write to bus.
        '''
        self._tx_queue.put_nowait(msg)
    
    
    def tx_thread(self):
        #TODO. Single handle still required? Blocking is essential.
        while False and self._threads_running.is_set():
            tx_msg = None
            have_lock = False
            try:
                # TODO
                if False and self.single_handle:
                    if not self._tx_queue.empty():
                        # Tell the rx thread to give up the can handle
                        # because we have a message to write to the bus
                        self.writing_event.set()
                        # Acquire a lock that the rx thread has started waiting on
                        self.done_writing.acquire()
                        have_lock = True
                    else:
                        raise queue.Empty('')
                    
                while not self._tx_queue.empty():
                    tx_msg = self._tx_queue.get(timeout=None)
                    if tx_msg is not None:
                        self._put_message(tx_msg)
                        
            except queue.Empty:
                pass
            # TODO
            if False and self.single_handle and have_lock:
                self.writing_event.clear()
                # Tell the rx thread it can start again
                self.done_writing.notify()
                self.done_writing.release()
                have_lock = False

    
    def rx_thread(self):
        """
        The consumer thread.
        """
        while self._threads_running.is_set():
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
        self._threads_running.clear()


    __metaclass__ = abc.ABCMeta

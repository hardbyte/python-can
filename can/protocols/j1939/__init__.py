"""
SAE J1939 vehicle bus standard.

http://en.wikipedia.org/wiki/J1939
"""
import threading
try:
    from queue import Queue
except ImportError:
    from Queue import Queue

from can import Bus

from can.protocols.j1939.pdu import PDU


class J1939Bus(Bus):

    def __init__(self, pdu_type=PDU, *args, **kwargs):
        self._pdu_type = pdu_type
        self._long_message_throttler = threading.Thread(target=self._throttler_function)
        self._incomplete_received_pdus = {}
        self._incomplete_received_pdu_lengths = {}
        self._incomplete_transmitted_pdus = {}
        self._long_message_segment_queue = Queue(0)
        self._long_message_segment_interval = long_message_segment_interval
        
        super(J1939Bus, self).__init__(*args, **kwargs)
        
        self._long_message_throttler.start()
        
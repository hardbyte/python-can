# -*- coding: utf-8 -*-

import abc
from constants import *

class BusABC(object):
    """CAN Bus Abstract Base Class

    Implementations must subclass and implement:
        - write method
        - __get_message method
        - channel_info attribute
    
    """
    
    
    def __init__(self, *args, **kwargs):
        pass
    
    # list of callbacks which will be passed Message instances.
    listeners = []
    
    # a string describing the channel
    channel_info = 'unknown'    
    
    @abc.abstractmethod
    def write(self, msg):
        pass 


    def write_for_period(self, messageGapInSeconds, totalPeriodInSeconds, message):
        pass


    def flush_tx_buffer(self):
        pass


    def shutdown(self):
        pass

    __metaclass__ = abc.ABCMeta

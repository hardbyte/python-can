import cPickle
import ipipe

from pycanlib import CAN

class ExtractTimeslice(ipipe.Pipe):
    def __init__(self, start_time=0.0, end_time=0.0):
        ipipe.Pipe.__init__(self)
        self.__start_time = start_time
        self.__end_time = end_time

    def __iter__(self):
        for _i, _item in enumerate(self.input):
            if (_item.timestamp >= self.__start_time) and (_item.timestamp <= self.__end_time):
                yield _item

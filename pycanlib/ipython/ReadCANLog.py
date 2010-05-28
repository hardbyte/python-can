import cPickle
import ipipe

from pycanlib import CAN

class ReadCANLog(ipipe.Table):

    def __init__(self, filename):
        ipipe.Table.__init__(None)
        with open(filename, "rb") as _infile:
            _log = cPickle.load(_infile)
        self.__messages = []
        for _msg_list in _log.message_lists:
            for _msg in _msg_list.messages:
                self.__messages.append(_msg)

    def __iter__(self):
        for _msg in self.__messages:
            yield _msg

import cPickle
import datetime
import ipipe
import os

from pycanlib import CAN

class LogCAN(ipipe.Display):

    def __init__(self, input=None):
        ipipe.Display.__init__(self, input)
        self.logStartTime = datetime.datetime.now()
        _timestamp = self.logStartTime.strftime("%Y%m%d_%H%M%S")
        _userdir = os.path.expanduser("~")
        _path = os.path.join(_userdir, "LogCAN")
        _datfilename = "LogCAN_%s.dat" % _timestamp
        if not os.path.exists(_path):
            os.makedirs(_path)
        self.datfilename = _datfilename
        self.msglist = []

    def display(self):
        print
        try:
            for item in ipipe.xiter(self.input):
                print item
                self.msglist.append(item)
        except KeyboardInterrupt:
            pass
        _log_info = CAN.LogInfo(log_start_time=self.logStartTime,
                                log_end_time=datetime.datetime.now(),
                                original_file_name=self.datfilename,
                                tester_name=os.getenv("USERNAME"))
        _machine_info = CAN.get_host_machine_info()
        _message_lists = [CAN.MessageList(messages=self.msglist)]
        _log_obj = CAN.Log(log_info=_log_info,
                           channel_info=None,
                           machine_info=_machine_info,
                           message_lists=_message_lists)
        with open(os.path.join(_path, self.datfilename), "w") as _datfile:
            cPickle.dump(_log_obj, _datfile)

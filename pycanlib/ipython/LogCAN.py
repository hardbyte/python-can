import cPickle
import datetime
import ipipe
import os.path

from pycanlib import CAN

class LogCAN(ipipe.Display):

    def __init__(self, input=None):
        ipipe.Display.__init__(self, input)
        self.logStartTime = datetime.datetime.now()
        _timestamp = self.logStartTime.__str__().replace("-", "")
        _timestamp = _timestamp.replace(" ", "").replace(":", "").replace(".", "")
        _userdir = os.path.expanduser("~")
        _path = os.path.join(_userdir, "LogCAN")
        _tdvfilename = "LogCAN-%s.log" % _timestamp
        _datfilename = "LogCAN-%s.dat" % _timestamp
        if not os.path.exists(os.path.dirname(_path)):
            os.makedirs(os.path.dirname(_path))
        self.datlogfile = open(os.path.join(_path, _datfilename), "w")
        self.tdvlogfile = open(os.path.join(_path, _tdvfilename), "w")
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
        cPickle.dump(_log_obj, self.datlogfile)
        self.datlogfile.close()
        self.tdvlogfile.write("%s" % _log_obj)
        self.tdvlogfile.close()

import cPickle
import datetime
import ipipe
import os

from pycanlib import CAN

class WriteLog(ipipe.Display):

    def __init__(self, input=None):
        ipipe.Display.__init__(self, input)
        self.__start_time = datetime.datetime.now()
        self.msglist = []

    def display(self):
        print
        try:
            for item in ipipe.xiter(self.input):
                print item
                self.msglist.append(item)
        except KeyboardInterrupt:
            pass
        CAN.Log(log_info=CAN.LogInfo(log_start_time=self.__start_time,
                                     log_end_time=datetime.datetime.now(),
                                     original_file_name=("can_message_log_%s.dat" % self.__start_time.strftime("%Y%m%d_%H%M%S")),
                                     tester_name=("%s" % os.getenv("USERNAME"))),
                channel_info=None,
                machine_info=CAN.get_host_machine_info(),
                message_lists=[CAN.MessageList(messages=self.msglist)]).write_to_file(path=os.path.expanduser(os.path.join("~", "WriteLog")))

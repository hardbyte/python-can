"""
WriteLog.py: an ipython utility which logs traffic streams in ipython
to a file on disk.

Copyright (C) 2010 Dynamic Controls

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

Contact details
---------------

Postal address:
    Dynamic Controls
    17 Print Place
    Addington
    Christchurch 8024
    New Zealand

E-mail: bpowell AT dynamiccontrols DOT com
"""
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

"""
ReadLog.py: an ipython utility used to read logged messages from
pickled log files.

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
import ipipe

from pycanlib import CAN

class ReadLog(ipipe.Table):

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

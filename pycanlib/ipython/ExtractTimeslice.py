"""
ExtractTimeslice.py: an ipython utility used to extract a "timeslice" of
a CAN traffic stream (that is, the messages in that stream with timestamps
between the specified start and end times).

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

class ExtractTimeslice(ipipe.Pipe):
    def __init__(self, start_time=0.0, end_time=0.0):
        ipipe.Pipe.__init__(self)
        self.__start_time = start_time
        self.__end_time = end_time

    def __iter__(self):
        for _i, _item in enumerate(self.input):
            if (_item.timestamp >= self.__start_time) and (_item.timestamp <= self.__end_time):
                yield _item

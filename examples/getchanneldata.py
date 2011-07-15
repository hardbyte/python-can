"""
getchanneldata.py: an example script illustrating access to
channel data available for a CAN bus channels connected to a
computer.

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
import ctypes
import sys
import time

from pycanlib import CAN, canlib

if __name__ == "__main__":
    print CAN.get_host_machine_info()
    _num_channels = ctypes.c_int(0)
    canlib.canGetNumberOfChannels(ctypes.byref(_num_channels))
    for _channel in xrange(0, _num_channels.value):
        _bus = CAN.Bus(_channel, 1000000, 4, 3, 1, 3)
        print _bus.channel_info
        _bus.shutdown()


time.sleep(1)

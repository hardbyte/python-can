"""
ReadCAN.py: an ipython utility used to read CAN traffic from a CAN
bus handle (physical or virtual).

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
import ipipe
import Queue
import time

from pycanlib import CAN, canlib

class ReadCAN(ipipe.Table):

    def __init__(self, channel, bitrate, tseg1, tseg2, sjw, no_samp, driver_mode=CAN.DRIVER_MODE_NORMAL):
        ipipe.Table.__init__(None)
        self.__bus = CAN.Bus(channel=channel, bitrate=bitrate, tseg1=tseg1, tseg2=tseg2, sjw=sjw, no_samp=no_samp, driver_mode=driver_mode)
        self.__reader = CAN.BufferedReader()
        self.__bus.add_listener(self.__reader)

    def __iter__(self):
        try:
            while True:
                _msg = self.__reader.get_message()
                if _msg != None:
                    yield _msg
        except KeyboardInterrupt:
            self.__bus.shutdown()


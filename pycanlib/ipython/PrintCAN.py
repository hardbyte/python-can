"""
PrintCAN.py: an ipython utility used to print streams of CAN messages
generated in ipython.

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
import time

from pycanlib import CAN

class PrintCAN(ipipe.Display):

    def __init__(self, input=None):
        ipipe.Display.__init__(self, input)

    def display(self):
        print
        try:
            for item in ipipe.xiter(self.input):
                print item
        except KeyboardInterrupt:
            time.sleep(1)

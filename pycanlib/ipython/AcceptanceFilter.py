"""
AcceptanceFilter.py: an ipython utility used to perform acceptance filtering
on a stream of CAN traffic generated in ipython.

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

from pycanlib import CAN

class AcceptanceFilter(ipipe.Pipe):
    def __init__(self, std_acceptance_code=0, std_acceptance_mask=CAN.STD_ACCEPTANCE_MASK_ALL_BITS, ext_acceptance_code=0, ext_acceptance_mask=CAN.EXT_ACCEPTANCE_MASK_ALL_BITS):
        ipipe.Pipe.__init__(self)
        self.__filter = CAN.AcceptanceFilter(std_acceptance_code=std_acceptance_code, std_acceptance_mask=std_acceptance_mask, ext_acceptance_code=ext_acceptance_code, ext_acceptance_mask=ext_acceptance_mask)

    def __iter__(self):
        for _i, _item in enumerate(self.input):
            _item = self.__filter.filter_message(_item)
            if _item != None:
                yield _item

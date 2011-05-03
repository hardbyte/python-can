"""
dat2tdv.py: part of pycanlib, converts pickled (*.dat) log files generated
by can_logger.py and the WriteLog ipython utility to human-readable
tab-delimited values (TDV) format.

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
import os
import sys

from pycanlib import CAN

if __name__ == "__main__":
    if len(sys.argv) > 1:
        try:
            with open(sys.argv[1], "rb") as _in_file:
                _log = cPickle.load(_in_file)
            _path = os.path.dirname(sys.argv[1])
            if len(_path) == 0:
                _path = "./"
            _log.write_to_file(format=CAN.LOG_FORMAT_TDV, name=("%s.log" % os.path.splitext(sys.argv[1])[0]), path=_path)
        except IOError:
            sys.stderr.write("ERROR: Input file %s not found\n" % sys.argv[1])

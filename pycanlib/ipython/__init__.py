"""
ipython/__init__.py

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
def doIPythonImports(ip_engine):
    ip_engine.ex("print 'Importing ipipe library...'")
    ip_engine.ex("from ipipe import *")
    ip_engine.ex("print 'Importing pycanlib IPython extensions...'")
    ip_engine.ex("print '\tReadCAN...'")
    ip_engine.ex("from pycanlib.ipython.ReadCAN import *")
    ip_engine.ex("print '\tWriteCAN...'")
    ip_engine.ex("from pycanlib.ipython.WriteCAN import *")
    ip_engine.ex("print '\tPrintCAN...'")
    ip_engine.ex("from pycanlib.ipython.PrintCAN import *")
    ip_engine.ex("print '\tReadLog...'")
    ip_engine.ex("from pycanlib.ipython.ReadLog import *")
    ip_engine.ex("print '\tWriteLog...'")
    ip_engine.ex("from pycanlib.ipython.WriteLog import *")
    ip_engine.ex("print '\tAcceptanceFilter...'")
    ip_engine.ex("from pycanlib.ipython.AcceptanceFilter import *")
    ip_engine.ex("print '\tExtractTimeslice...'")
    ip_engine.ex("from pycanlib.ipython.ExtractTimeslice import *")

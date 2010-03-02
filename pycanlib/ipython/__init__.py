"""
Module: pycanlib/ipython

This module provides ipython/ipipe support for pycanlib. This file contains
the method used to import the ipython/ipipe pycanlib support classes into 
ipython.
"""

def doIPythonImports(ip_engine):
    """
    Method: doIPythonImports
    
    This function is called by the startup script for the ipython pycanlib 
    profile, and imports the ipython pycanlib support files into the ipython 
    scripting engine.
    
    Inputs:
        ip_engine: the ipython scripting engine.
    """
    ip_engine.ex("print 'Importing ipipe library...'")
    ip_engine.ex("from ipipe import *")
    ip_engine.ex("print 'Importing pycanlib IPython extensions...'")
    ip_engine.ex("print '\tReadCAN...'")
    ip_engine.ex("from pycanlib.ipython.ReadCAN import *")
    ip_engine.ex("print '\tWriteCAN...'")
    ip_engine.ex("from pycanlib.ipython.WriteCAN import *")
    ip_engine.ex("print '\tPrintCAN...'")
    ip_engine.ex("from pycanlib.ipython.PrintCAN import *")
    ip_engine.ex("print '\tLogCAN...'")
    ip_engine.ex("from pycanlib.ipython.LogCAN import *")
#    ip_engine.ex("print '\tReadCANLog...'")
#    ip_engine.ex("from pycanlib.ipython.ReadCANLog import *")
#    ip_engine.ex("print '\tReadSSTLog...'")
#    ip_engine.ex("from pycanlib.ipython.ReadSSTLog import *")
#    ip_engine.ex("print '\tFilterDevices...'")
#    ip_engine.ex("from pycanlib.ipython.FilterDevices import *")
#    ip_engine.ex("print '\tExtractTimeslice...'")
#    ip_engine.ex("from pycanlib.ipython.ExtractTimeslice import *")

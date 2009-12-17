"""
File: ipy_profile_pycanlib.py

This file is the ipython profile used to load pycanlib ipython extensions.
It must be installed in the ~/_ipython/ folder on Windows or the 
~/.ipython/ folder on Linux, where ~ is the user's home folder.
"""
import IPython.ipapi
import pycanlib.ipython

ip_engine = IPython.ipapi.get()
ip_engine.options.autocall = 2
pycanlib.ipython.doIPythonImports(ipEngine)

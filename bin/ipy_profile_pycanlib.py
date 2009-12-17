"""
File: ipy_profile_pycanlib.py

This file is the ipython profile used to load pycanlib ipython extensions.
"""
import IPython.ipapi
import pycanlib.ipython

ip_engine = IPython.ipapi.get()
ip_engine.options.autocall = 2
pycanlib.ipython.doIPythonImports(ip_engine)

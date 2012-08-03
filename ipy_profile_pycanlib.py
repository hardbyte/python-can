"""
Used to load the pycanlib ipython extensions when the pycanlib ipython
profile is used.
"""

import IPython.ipapi
import pycanlib.ipython

ip_engine = IPython.ipapi.get()
ip_engine.options.autocall = 2
pycanlib.ipython.doIPythonImports(ip_engine)

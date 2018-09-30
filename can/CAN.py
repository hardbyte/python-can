# coding: utf-8

"""
This module was once the core of python-can, containing
implementations of all the major classes in the library, now
however all functionality has been refactored out. This API
is left intact for version 2.x to aide with migration.

WARNING:
This module is deprecated an will get removed in version 3.x.
Please use ``import can`` instead.
"""

from __future__ import absolute_import

from can.message import Message
from can.listener import Listener, BufferedReader, RedirectReader
from can.util import set_logging_level
from can.io import *

import warnings

# See #267.
# Version 2.0 - 2.1:    Log a Debug message
# Version 2.2:          Log a Warning
# Version 3.x:          DeprecationWarning
# Version 4.0:          Remove the module
warnings.warn('Loading python-can via the old "CAN" API is deprecated since v3.0 an will get removed in v4.0 '
              'Please use `import can` instead.', DeprecationWarning)

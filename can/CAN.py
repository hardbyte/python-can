#!/usr/bin/env python
# coding: utf-8

"""
This module was once the core of python-can, containing
implementations of all the major classes in the library, now
however all functionality has been refactored out. This API
is left intact for version 2.0 to 2.3 to aide with migration.

WARNING:
This module is deprecated an will get removed in version 2.4.
Please use ``import can`` instead.
"""

from __future__ import absolute_import

from can.message import Message
from can.listener import Listener, BufferedReader, RedirectReader
from can.util import set_logging_level
from can.io import *

import logging

log = logging.getLogger('can')

# See #267
# Version 2.0 - 2.1:    Log a Debug message
# Version 2.2:          Log a Warning
# Version 2.3:          Log an Error
# Version 2.4:          Remove the module
log.warning('Loading python-can via the old "CAN" API is deprecated since v2.0 an will get removed in v2.4. '
            'Please use `import can` instead.')

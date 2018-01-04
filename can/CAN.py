"""
This module was once the core of python-can, containing
implementations of all the major classes in the library, now
however all functionality has been refactored out. This api
is left intact for version 2.0 to aide with migration.
"""
from __future__ import absolute_import

from can.message import Message
from can.listener import Listener, BufferedReader, RedirectReader
from can.util import set_logging_level
from can.io import *

import logging

log = logging.getLogger('can')
log.info("Loading python-can via the old CAN api")

#!/usr/bin/env python
# coding: utf-8

"""
This module was moved to ``can.scripts.logger``.
``can.logger`` will be removed in a future version.
"""

from __future__ import absolute_import

from warnings import warn

from .scripts.logger import main


if __name__ == "__main__":
    warn("this module was moved to can.scripts.logger; can.logger will be removed in a future version",
         DeprecationWarning)
    main()

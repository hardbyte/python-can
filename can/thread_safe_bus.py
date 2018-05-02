#!/usr/bin/env python
# coding: utf-8

"""
"""

from __future__ import print_function, absolute_import

from abc import ABCMeta, abstractmethod
import threading


class ThreadSafeBus(object):
    """
    Contains a thread safe :class:`~can.BusABC` implementation that
    wraps around an existing interface instance.

    This approach assumes that both :meth:`~can.BusABC.send` and
    :meth:`~can.BusABC.recv` of the underlying .
    """
    pass

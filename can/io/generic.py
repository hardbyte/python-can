#!/usr/bin/env python
# coding: utf-8

"""
Contains generic classes for file IO.
"""

from abc import ABCMeta, abstractmethod

from can import Listener


class BaseIOHandler(object):
    """A generic file handler that can be used for reading and writing.
    """

    __metaclass__ = ABCMeta

    def __init__(self, open_file, filename='can_data', mode='Urt'):
        """
        TODO docs
        """
        if open_file:
            self.file = open(filename, mode)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.stop()

    def stop(self):
        if hasattr(self, 'file') and self.file:
            # this also implies a flush()
            self.file.close()

#!/usr/bin/env python
# coding: utf-8

"""
Contains a generic class for file IO.
"""

from abc import ABCMeta, abstractmethod

from can import Listener


class BaseIOHandler(object):
    """A generic file handler that can be used for reading and writing.

    Can be used as a context manager.
    """

    __metaclass__ = ABCMeta

    def __init__(self, open_file, filename='can_data', mode='rt'):
        """
        :param bool open_file: opens a file if set to True
        :param str filename: the path/filename of the file to open
        :param str mode: the mode that should be used to open the file, see
                         :func:`builtin.open`
        """
        super(BaseIOHandler, self).__init__() # for multiple inheritance
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

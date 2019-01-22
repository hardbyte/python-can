# coding: utf-8

"""
Contains a generic class for file IO.
"""

from abc import ABCMeta, abstractmethod

from can import Listener


class BaseIOHandler(object):
    """A generic file handler that can be used for reading and writing.

    Can be used as a context manager.

    :attr file-like file:
        the file-like object that is kept internally, or None if none
        was opened
    """

    __metaclass__ = ABCMeta

    def __init__(self, file, mode='rt'):
        """
        :param file: a path-like object to open a file, a file-like object
                     to be used as a file or `None` to not use a file at all
        :param str mode: the mode that should be used to open the file, see
                         :func:`open`, ignored if *file* is `None`
        """
        if file is None or (hasattr(file, 'read') and hasattr(file, 'write')):
            # file is None or some file-like object
            self.file = file
        else:
            # file is some path-like object
            self.file = open(file, mode)

        # for multiple inheritance
        super(BaseIOHandler, self).__init__()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.stop()

    def stop(self):
        if self.file is not None:
            # this also implies a flush()
            self.file.close()

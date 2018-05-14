#!/usr/bin/env python
# coding: utf-8

"""
"""

from can import CanError


class VectorError(CanError):

    def __init__(self, error_code, error_string, function):
        self.error_code = error_code
        text = "%s failed (%s)" % (function, error_string)
        super(VectorError, self).__init__(text)

# coding: utf-8

"""
"""

from can import CanError


class VectorError(CanError):
    def __init__(self, error_code, error_string, function):
        self.error_code = error_code
        super().__init__(f"{function} failed ({error_string})")

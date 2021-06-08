"""
"""

from can import CanError


class VectorError(CanError):
    def __init__(self, error_code, error_string, function):
        super().__init__(
            message=f"{function} failed ({error_string})", error_code=error_code
        )

        # keep reference to args for pickling
        self._args = error_code, error_string, function

    def __reduce__(self):
        return VectorError, self._args, {}

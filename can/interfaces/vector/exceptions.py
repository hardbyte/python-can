from can import CanError


class VectorError(CanError):

    def __init__(self, error_code, error_string):
        self.error_code = error_code
        super(VectorError, self).__init__(error_string)

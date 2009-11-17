import logging


class NullHandler(logging.Handler):
    def emit(self, record):
        pass


h = NullHandler()
rootLogger = logging.getLogger("pycanlib")
rootLogger.addHandler(h)

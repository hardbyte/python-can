import threading
try:
    import queue
except ImportError:
    import Queue as queue

class Notifier(object):

    def __init__(self, bus, listeners):
        self.listeners = listeners
        self.bus = bus

        self.running = threading.Event()
        self.running.set()

        self._reader = threading.Thread(target=self.rx_thread)
        self._reader.daemon = True

        self._reader.start()

    def rx_thread(self):
        while self.running.is_set():
            msg = self.bus.recv()
            if msg is not None:
                for callback in listeners:
                    callback(msg)
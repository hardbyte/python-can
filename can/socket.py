import logging
import queue
import threading
import time
import copy

from functools import reduce
from operator import add

from .interface import Bus
from .bus import BusABC
from . import CanError
from .message import Message

log = logging.getLogger("can.socket")
log_autodetect = log.getChild("detect_available_configs")


class SocketsThreadPool:
    # pylint: disable=no-member
    __instance = None

    def __new__(cls):
        if SocketsThreadPool.__instance is None:
            SocketsThreadPool.__instance = object.__new__(cls)
            SocketsThreadPool.__instance.buses = dict()
            SocketsThreadPool.__instance.rx_threads = dict()
            SocketsThreadPool.__instance.tx_threads = dict()
            SocketsThreadPool.__instance.buses_mutex = threading.Lock()
        return SocketsThreadPool.__instance

    def recv_function(self, k):
        while True:
            with self.buses_mutex:
                try:
                    bus, _, _, sockets = self.buses[k]
                except KeyError:
                    return
            if not sockets:
                return
            msg = bus.recv(timeout=0.01)
            if msg is None:
                continue
            for sock in sockets:
                if sock._matches_filters(msg):
                    sock.rx_queue.put(copy.copy(msg))

    def send_function(self, k):
        while True:
            with self.buses_mutex:
                try:
                    bus, tx_queue, tx_signal, sockets = self.buses[k]
                except KeyError:
                    return
            if not sockets:
                return
            try:
                tx_signal.acquire()
                sender, msg = tx_queue.get(timeout=0.001)
            except queue.Empty:
                continue
            try:
                bus.send(msg)
                msg = copy.copy(msg)
                for sock in sockets:
                    msg.timestamp = time.time()
                    if sock != sender and sock._matches_filters(msg):
                        sock.rx_queue.put(msg)
            except CanError:
                continue

    def register(self, socket, *args, **kwargs):
        k = str(
            kwargs.get("bustype", "unknown_bustype")
            + "_"
            + kwargs.get("channel", "unknown_channel")
            + "_"
            + kwargs.get("interface", "unknown_interface")
        )
        if k in self.buses:
            bus, tx_queue, tx_signal, sockets = self.buses[k]
            sockets.append(socket)
            filters = [s.filters for s in sockets if s.filters is not None]
            if filters:
                bus.set_filters(reduce(add, filters))
            socket.tx_queue = tx_queue
            socket.tx_signal = tx_signal
            with self.buses_mutex:
                self.buses[k] = (bus, tx_queue, tx_signal, sockets)
        else:
            bus = Bus(*args, **kwargs)
            tx_queue = queue.Queue()
            tx_signal = threading.Semaphore(0)
            socket.tx_queue = tx_queue
            socket.tx_signal = tx_signal
            with self.buses_mutex:
                self.buses[k] = (bus, tx_queue, tx_signal, [socket])
            self.rx_threads[k] = threading.Thread(target=self.recv_function, args=(k,))
            self.tx_threads[k] = threading.Thread(target=self.send_function, args=(k,))
            self.rx_threads[k].start()
            self.tx_threads[k].start()

    def unregister(self, socket):
        for k, v in self.buses.copy().items():
            bus, tx_queue, tx_signal, sockets = v
            if socket in sockets:
                sockets.remove(socket)
            with self.buses_mutex:
                self.buses[k] = (bus, tx_queue, tx_signal, sockets)

        # give receiver thread time to exit recv with timeout
        time.sleep(0.01)

        for k, v in self.buses.copy().items():
            bus, _, tx_signal, sockets = v
            if not sockets:
                with self.buses_mutex:
                    del self.buses[k]
                tx_signal.release()
                self.rx_threads[k].join()
                self.tx_threads[k].join()
                bus.shutdown()
                del self.rx_threads[k]
                del self.tx_threads[k]


class Socket(BusABC):
    """Socket for specific Bus or Interface.
    """

    def __init__(self, *args, **kwargs) -> None:
        super(Socket, self).__init__(*args, **kwargs)
        self.rx_queue = queue.Queue() # type: queue.Queue[Message]
        self.tx_queue = None
        self.tx_signal = None
        SocketsThreadPool().register(self, *args, **kwargs)

    def _recv_internal(self, timeout):
        try:
            return self.rx_queue.get(block=True, timeout=timeout), True
        except queue.Empty:
            return None, True

    def send(self, msg, timeout=None):
        try:
            self.tx_queue.put((self, msg), block=True, timeout=timeout)
            self.tx_signal.release()
        except queue.Full:
            raise CanError

    def shutdown(self):
        SocketsThreadPool().unregister(self)

    @staticmethod
    def select(sockets, *args, **kwargs):
        return [s for s in sockets if not s.rx_queue.empty()], [], []

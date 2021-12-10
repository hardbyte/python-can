from time import sleep
import cfuc
from can import Message
import threading

c = cfuc.cfucBus("COM50", 100 * 1000)

m = Message(
    0,
    0x11223344,
    True,
    False,
    False,
    None,
    5,
    bytearray(b"\x01\x02\x03\x04\x05"),
    False,
    False,
    False,
    None,
    False,
)
c.send(m, None)


def rx_function(caninterface):
    retry = 0
    while retry < 60:
        caninterface._recv_internal(0)
        retry = retry + 1


x = threading.Thread(target=rx_function, args=(c,))
x.start()

x.join()

c.shutdown()

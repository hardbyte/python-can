import ipipe
import Queue

from pycanlib import CAN

class ReadCAN(ipipe.Table):

    def __init__(self, channel, speed, tseg1, tseg2, sjw, no_samp):
        ipipe.Table.__init__(None)
        self.__bus = CAN.Bus(channel=channel, speed=speed, tseg1=tseg1, tseg2=tseg2, sjw=sjw, no_samp=no_samp)
        self.__reader = CAN.BufferedReader()
        self.__bus.add_listener(self.__reader)

    def __iter__(self):
        try:
            while True:
                _msg = self.__reader.get_message()
                if _msg != None:
                    yield _msg
        except KeyboardInterrupt:
            pass

import ipipe
import Queue

from pycanlib import CAN, canlib

class ReadCAN(ipipe.Table):

    def __init__(self, channel, bitrate, tseg1, tseg2, sjw, no_samp, driver_mode=canlib.canDRIVER_NORMAL):
        ipipe.Table.__init__(None)
        self.__bus = CAN.Bus(channel=channel, bitrate=bitrate, tseg1=tseg1, tseg2=tseg2, sjw=sjw, no_samp=no_samp, driver_mode=driver_mode)
        self.__reader = CAN.BufferedReader()
        self.__bus.add_listener(self.__reader)

    def __iter__(self):
        while True:
            _msg = self.__reader.get_message()
            if _msg != None:
                yield _msg

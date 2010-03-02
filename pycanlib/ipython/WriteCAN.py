import ipipe

from pycanlib import CAN

class WriteCAN(ipipe.Display):

    def __init__(self, channel, speed, tseg1, tseg2, sjw, no_samp, input=None):
        self.__bus = CAN.Bus(channel, speed, tseg1, tseg2, sjw, no_samp)
        ipipe.Display.__init__(self, input)

    def display(self):
        print
        for item in ipipe.xiter(self.input):
            try:
                self.__bus.write(item)
            except KeyboardInterrupt:
                break

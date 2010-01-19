import ipipe
import sys, time

from pycanlib import CAN, canlib

class ReadCAN(ipipe.Table):

    def __init__(self, channel, speed, tseg1, tseg2, sjw, no_samp):
        ipipe.Table.__init__(None)
        self.bus = CAN.Bus(channel=channel, speed=speed, tseg1=tseg1, 
          tseg2=tseg2, sjw=sjw, no_samp=no_samp)
        self.bus.enable_callback()

    def __iter__(self):
        while True:
            try:
                message = self.bus.read()
                if message != None:
                    yield message
                else:
                    time.sleep(0.001)
            except KeyboardInterrupt:
                self.bus.shutdown()
                break
            except:
                self.bus.shutdown()
                break

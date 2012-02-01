"""
PrintCAN.py: an ipython utility used to print streams of CAN messages
generated in ipython.
"""
import ipipe
import time

from pycanlib import CAN

class PrintCAN(ipipe.Display):

    def __init__(self, input=None):
        ipipe.Display.__init__(self, input)

    def display(self):
        print
        try:
            for item in ipipe.xiter(self.input):
                print item
        except KeyboardInterrupt:
            time.sleep(1)

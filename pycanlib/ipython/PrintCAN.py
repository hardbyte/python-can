import ipipe

from pycanlib import CAN

class PrintCAN(ipipe.Display):

    def __init__(self, input=None):
        ipipe.Display.__init__(self, input)

    def display(self):
        print
        for item in ipipe.xiter(self.input):
            try:
                print item
            except KeyboardInterrupt:
                break

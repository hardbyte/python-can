"""
File: PrintCAN.py

This file contains a subclass of ipipe.Display that can be used to print 
CAN traffic to the ipython terminal window.
"""
import ipipe

from pycanlib import CAN

class PrintCAN(ipipe.Display):
    """
    Class: PrintCAN
    
    Subclass of ipipe.Display used to print CAN traffic to the ipython 
    terminal.
    
    Parent class: ipipe.Display
    """
    def __init__(self, input=None):
        """
        Constructor: PrintCAN

        Inputs:
            input [optional, default=None]: previous stage of the pipeline 
            (see ipipe documentation for more details - 
             http://projects.scipy.org/ipython/ipython/wiki/UsingIPipe).
        """
        ipipe.Display.__init__(self, input)

    def display(self):
        """Method: display
        Prints received messages to terminal
        
        Inputs: None
        """
        print
        for item in ipipe.xiter(self.input):
            try:
                print item
            except KeyboardInterrupt:
                break

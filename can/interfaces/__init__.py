# -*- coding: utf-8 -*-
"""
Interfaces contain low level implementations that interact with CAN hardware.

TODO: Additionally they can extend the argparser used so command line arguments
can set the bus properties for a given backend.
"""
import can


def _add_subparsers(parser):
    """
    
    """
    
    subparsers = parser.add_subparsers(dest="interface", #default=can.rc['interface'], 
                                       help='''The CAN interface to use. Note that depending on the
                                       interface their may be different command line arguments.''')
    
    # create the parser for each interface
    kparser = subparsers.add_parser('kvaser', help='Kvaser interface')
    
    from .kvaser import argument_parser
    argument_parser.add_to_parser(kparser)
    
    sparser = subparsers.add_parser('serial', help='Serial interface')
    sparser.add_argument('channel', help="The serial device. E.g /dev/rfcomm0")


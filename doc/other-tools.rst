Other CAN bus tools
===================

In order to keep the project maintainable, the scope of the module is limited to providing common
abstractions to different hardware devices, and a basic suite of utilities for sending and
receiving messages on a CAN bus. Other tools are available that either extend the functionality
of python-can, or provide complementry features that an engineer dealing with CAN will find useful.

Some of these tools are listed below for convenience.

CAN Message protocols
---------------------

#. SAE J1939 Message Protocol
    * The `can-j1939`_ module provides an implementation of the CAN SAE J1939 standard for Python,
      including J1939-22. `can-j1939`_ uses python-can to provide support for multiple hardware
      interfaces.
    .. _can-j1939: https://github.com/juergenH87/python-can-j1939
#. CIA CANopen
    * The `canopen`_ module provides an implementation of the CIA CANopen protocol, aiming to be
      used for automation and testing purposes
    .. _canopen: https://github.com/christiansandberg/canopen
#. ISO 15765-2 (ISO TP)
    * The `can-isotp`_ module provides an implementation of the ISO TP CAN protocol for sending
      data packets via a CAN transport layer.
    .. _can-isotp: https://github.com/pylessard/python-can-isotp

CAN Frame Parsing tools etc.
----------------------------

#. CAN Message Decoding
    * The `canmatrix`_ module provides methods for converting between multiple popular message
      frame definition file formats (e.g. .DBC files, .KCD files etc.
    .. _canmatrix: https://github.com/ebroecker/canmatrix

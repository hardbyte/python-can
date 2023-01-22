Other CAN bus tools
===================

In order to keep the project maintainable, the scope of the package is limited to providing common
abstractions to different hardware devices, and a basic suite of utilities for sending and
receiving messages on a CAN bus. Other tools are available that either extend the functionality
of python-can, or provide complementary features that python-can users might find useful.

Some of these tools are listed below for convenience.

CAN Message protocols (implemented in Python)
---------------------------------------------

#. SAE J1939 Message Protocol
    * The `can-j1939`_ module provides an implementation of the CAN SAE J1939 standard for Python,
      including J1939-22. `can-j1939`_ uses python-can to provide support for multiple hardware
      interfaces.
#. CIA CANopen
    * The `canopen`_ module provides an implementation of the CIA CANopen protocol, aiming to be
      used for automation and testing purposes
#. ISO 15765-2 (ISO TP)
    * The `can-isotp`_ module provides an implementation of the ISO TP CAN protocol for sending
      data packets via a CAN transport layer.

#. UDS
    * The `python-uds`_ module is a communication protocol agnostic implementation of the Unified
      Diagnostic Services (UDS) protocol defined in ISO 14229-1, although it does have extensions
      for performing UDS over CAN utilising the ISO TP protocol. This module has not been updated
      for some time. 
    * The `uds`_ module is another tool that implements the UDS protocol, although it does have
      extensions for performing UDS over CAN utilising the ISO TP protocol. This module has not
      been updated for some time.
#. XCP
    * The `pyxcp`_ module implements the Universal Measurement and Calibration Protocol (XCP).
      The purpose of XCP is to adjust parameters and acquire current values of internal
      variables in an ECU.
	  
.. _can-j1939: https://github.com/juergenH87/python-can-j1939
.. _canopen: https://canopen.readthedocs.io/en/latest/
.. _can-isotp: https://can-isotp.readthedocs.io/en/latest/
.. _python-uds: https://python-uds.readthedocs.io/en/latest/index.html
.. _uds: https://uds.readthedocs.io/en/latest/
.. _pyxcp: https://pyxcp.readthedocs.io/en/latest/

CAN Frame Parsing tools etc. (implemented in Python)
----------------------------------------------------

#. CAN Message / Database scripting
    * The `cantools`_ package provides multiple methods for interacting with can message database
      files, and using these files to monitor live busses with a command line monitor tool.
#. CAN Message / Log Decoding
    * The `canmatrix`_ module provides methods for converting between multiple popular message
      frame definition file formats (e.g. .DBC files, .KCD files, .ARXML files etc.).
    * The `pretty_j1939`_ module can be used to post-process CAN logs of J1939 traffic into human
      readable terminal prints or into a JSON file for consumption elsewhere in your scripts.

.. _cantools: https://cantools.readthedocs.io/en/latest/
.. _canmatrix: https://canmatrix.readthedocs.io/en/latest/
.. _pretty_j1939: https://github.com/nmfta-repo/pretty_j1939

Other CAN related tools, programs etc.
--------------------------------------

#. Micropython CAN class
    * A `CAN class`_ is available for the original micropython pyboard, with much of the same
      functionality as is available with python-can (but with a different API!).
#. ASAM MDF Files
    * The `asammdf`_ module provides many methods for processing ASAM (Association for
      Standardization of Automation and Measuring Systems) MDF (Measurement Data Format) files.

.. _`CAN class`: https://docs.micropython.org/en/latest/library/pyb.CAN.html
.. _`asammdf`: https://asammdf.readthedocs.io/en/master/

|
|

.. note::
   See also the available plugins for python-can in :ref:`plugin interface`.


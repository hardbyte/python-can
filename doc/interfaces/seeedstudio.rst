.. _seeeddoc:


Seeed Studio USB-CAN Analyzer
=============================

SKU: 114991193

Links:

- https://www.seeedstudio.com/USB-CAN-Analyzer-p-2888.html
- https://github.com/SeeedDocument/USB-CAN_Analyzer
- https://copperhilltech.com/blog/usbcan-analyzer-usb-to-can-bus-serial-protocol-definition/


Installation
------------

This interface has additional dependencies which can be installed using pip and the optional extra ``seeedstudio``.  That will include the dependency ``pyserial``::

  pip install python-can[seeedstudio]



Interface
---------

::

    can.interfaces.seeedstudio.SeeedBus

A bus example::

    bus = can.interface.Bus(interface='seeedstudio', channel='/dev/ttyUSB0', bitrate=500000)



Configuration
-------------
::

 SeeedBus(channel,
          baudrate=2000000,
          timeout=0.1,
          frame_type='STD',
          operation_mode='normal',
          bitrate=500000,
          can_filters = [dict(can_id = 0x00, can_mask = 0x00)])

CHANNEL
 The serial port created by the USB device when connected.

TIMEOUT
 Only used by the underling serial port, it probably should not be changed.  The serial port baudrate=2000000 and rtscts=false are also matched to the device so are not added here.

FRAMETYPE
 - "STD"
 - "EXT"

OPERATIONMODE
 - "normal"
 - "loopback"
 - "silent"
 - "loopback_and_silent"

BITRATE
 - 1000000
 - 800000
 - 500000
 - 400000
 - 250000
 - 200000
 - 125000
 - 100000
 - 50000
 - 20000
 - 10000
 - 5000

CAN_FILTERS
  A list of can filter dictionaries. Defaults to the value
  ``[{"can_id": 0x00, "can_mask": 0x00}]`` (i.e. no filtering).
  An example filter: ``[{"can_id": 0x11, "can_mask": 0x21}]``

  **Hardware Limitation:** The Seeed Studio device only supports
  a single hardware filter. This list must contain at most
  one filter dictionary. A ``can.CanInitializationError`` will be
  raised if more than one filter is provided.

  Each filter dictionary should have the following keys:
  - ``can_id``: The CAN ID to filter on.
  - ``can_mask``: The mask to apply to the ID.

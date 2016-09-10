CAN Interface Modules
---------------------

**python-can** hides the low-level, device-specific interfaces to controller
area network adapters in interface dependant modules. However as each hardware
device is different, you should carefully go through your interface's
documentation.

The interfaces currently available are:

+---------------------+-------------------------------------+
| Name                | Documentation                       |
+=====================+=====================================+
| ``"socketcan"``     | :doc:`interfaces/socketcan`         |
+---------------------+-------------------------------------+
| ``"kvaser"``        | :doc:`interfaces/kvaser`            |
+---------------------+-------------------------------------+
| ``"serial"``        | :doc:`interfaces/serial`            |
+---------------------+-------------------------------------+
| ``"ixxat"``         | :doc:`interfaces/ixxat`             |
+---------------------+-------------------------------------+
| ``"pcan"``          | :doc:`interfaces/pcan`              |
+---------------------+-------------------------------------+
| ``"usb2can"``       | :doc:`interfaces/usb2can`           |
+---------------------+-------------------------------------+
| ``"virtual"``       | :doc:`interfaces/virtual`           |
+---------------------+-------------------------------------+

The `Interface Name` is used in :doc:`configuration`.


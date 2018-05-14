Vector
======

This interface adds support for CAN controllers by `Vector`_.

By default this library uses the channel configuration for CANalyzer.
To use a different application, open Vector Hardware Config program and create
a new application and assign the channels you may want to use.
Specify the application name as ``app_name='Your app name'`` when constructing
the bus or in a config file.

Channel should be given as a list of channels starting at 0.

Here is an example configuration file connecting to CAN 1 and CAN 2 for an
application named "python-can"::

    [default]
    interface = vector
    channel = 0, 1
    app_name = python-can

If you are using Python 2.7 it is recommended to install pywin32_, otherwise a
slow and CPU intensive polling will be used when waiting for new messages.


Bus
---

.. autoclass:: can.interfaces.vector.VectorBus

.. autoexception:: can.interfaces.vector.VectorError


.. _Vector: https://vector.com/
.. _pywin32: https://sourceforge.net/projects/pywin32/

Internal API
============

Here we document the odds and ends that are more helpful for creating your own interfaces
or listeners but generally shouldn't be required to interact with python-can.


Bus Internals
-------------

Several methods are not documented in the main :class:`can.BusABC`
as they are primarily useful for library developers as opposed to
library users.


.. class:: can.BusABC
    .. automethod:: _recv_internal


IO Utilities
------------


.. automodule:: can.io.generic
    :members:



Other Util
----------


.. automodule:: can.util
    :members:


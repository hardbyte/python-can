Internal API
============

Here we document the odds and ends that are more helpful for creating your own interfaces
or listeners but generally shouldn't be required to interact with python-can.


.. _businternals:


Extending the ``BusABC`` class
------------------------------

Concrete implementations **must** implement the following:
    * :meth:`~can.BusABC.send` to send individual messages
    * :meth:`~can.BusABC._recv_internal` to receive individual messages
      (see note below!)
    * set the :attr:`~can.BusABC.channel_info` attribute to a string describing
      the underlying bus and/or channel

They **might** implement the following:
    * :meth:`~can.BusABC.flush_tx_buffer` to allow discarding any
      messages yet to be sent
    * :meth:`~can.BusABC.shutdown` to override how the bus should
      shut down
    * :meth:`~can.BusABC._send_periodic_internal` to override the software based
      periodic sending and push it down to the kernel or hardware.
    * :meth:`~can.BusABC._apply_filters` to apply efficient filters
      to lower level systems like the OS kernel or hardware.
    * :meth:`~can.BusABC._detect_available_configs` to allow the interface
      to report which configurations are currently available for new
      connections.
    * :meth:`~can.BusABC.state` property to allow reading and/or changing
      the bus state.

.. note::

    *TL;DR*: Only override :meth:`~can.BusABC._recv_internal`,
    never :meth:`~can.BusABC.recv` directly.

    Previously, concrete bus classes had to override :meth:`~can.BusABC.recv`
    directly instead of :meth:`~can.BusABC._recv_internal`, but that has
    changed to allow the abstract base class to handle in-software message
    filtering as a fallback. All internal interfaces now implement that new
    behaviour. Older (custom) interfaces might still be implemented like that
    and thus might not provide message filtering:



Concrete instances are usually created by :class:`can.Bus` which takes the users
configuration into account.


Bus Internals
~~~~~~~~~~~~~

Several methods are not documented in the main :class:`can.BusABC`
as they are primarily useful for library developers as opposed to
library users. This is the entire ABC bus class with all internal
methods:

.. autoclass:: can.BusABC
    :private-members:
    :special-members:
    :noindex:



IO Utilities
------------


.. automodule:: can.io.generic
    :members:



Other Util
----------


.. automodule:: can.util
    :members:


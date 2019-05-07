.. _internalapi:

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



About the IO module
-------------------

Handling of the different file formats is implemented in :mod:`can.io`.
Each file/IO type is within a separate module and ideally implements both a *Reader* and a *Writer*.
The reader usually extends :class:`can.io.generic.BaseIOHandler`, while
the writer often additionally extends :class:`can.Listener`,
to be able to be passed directly to a :class:`can.Notifier`.



Adding support for new file formats
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This assumes that you want to add a new file format, called *canstore*.
Ideally add both reading and writing support for the new file format, although this is not strictly required.

1. Create a new module: *can/io/canstore.py*
   (*or* simply copy some existing one like *can/io/csv.py*)
2. Implement a reader ``CanstoreReader`` (which often extends :class:`can.io.generic.BaseIOHandler`, but does not have to).
   Besides from a constructor, only ``__iter__(self)`` needs to be implemented.
3. Implement a writer ``CanstoreWriter`` (which often extends :class:`can.io.generic.BaseIOHandler` and :class:`can.Listener`, but does not have to).
   Besides from a constructor, only ``on_message_received(self, msg)`` needs to be implemented.
4. Add a case to ``can.io.player.LogReader``'s ``__new__()``.
5. Document the two new classes (and possibly additional helpers) with docstrings and comments.
   Please mention features and limitations of the implementation.
6. Add a short section to the bottom of *doc/listeners.rst*.
7. Add tests where appropriate, for example by simply adding a test case called
   `class TestCanstoreFileFormat(ReaderWriterTest)` to *test/logformats_test.py*.
   That should already handle all of the general testing.
   Just follow the way the other tests in there do it.
8. Add imports to *can/__init__py* and *can/io/__init__py* so that the
   new classes can be simply imported as *from can import CanstoreReader, CanstoreWriter*.



IO Utilities
~~~~~~~~~~~~


.. automodule:: can.io.generic
    :members:



Other Utilities
---------------


.. automodule:: can.util
    :members:

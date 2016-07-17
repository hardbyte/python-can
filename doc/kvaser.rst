.. _kvaserdoc:

Kvaser's CANLIB
===============


Bus
---

.. autoclass:: can.interfaces.kvaser.canlib.KvaserBus


Internals
---------

The Kvaser :class:`~can.Bus` object with a physical CAN Bus can be operated in two
modes; ``single_handle`` mode with one shared bus handle used for both reading and
writing to the CAN bus, or with two separate bus handles.


.. warning:: Any objects inheriting from `Bus`_ should *not* directly
        use the interface handle(/s).


Threading
~~~~~~~~~

To avoid contention for the bus handle in ``single_handle`` mode, access is protected for
the **read** and **write** daemon threads with a ``writing_event`` *Event* and a
``done_writing`` *Condition*.

The read thread acquires ``done_writing`` and while ``writing_event`` is set
blocks waiting on the ``done_writing`` Condition. A 1ms blocking read is carried
out before ``done_writing`` is released.

The write thread blocks for 5ms on a queue (to allow the thread to stop). If
a message was received it *sets* the writing_event to tell the read thread
that a message in waiting to be sent. The ``done_writing`` is acquired for
the actual write, the writing_event is cleared and the ``done_writing`` event
is notified to start the read thread again.

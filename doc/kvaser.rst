.. _kvaserdoc:

Kvaser's CANLIB
===============


Bus
---

.. autoclass:: can.interfaces.kvaser.canlib.KvaserBus


Internals
---------

The Kvaser :class:`~can.Bus` object with a physical CAN Bus has one bus handle which is shared
by the read and write daemon threads. The access is protected with the
``writing_event`` *Event* and the ``done_writing`` *Condition*.

The read thread acquires ``done_writing`` and while ``writing_event`` is set
blocks waiting on the ``done_writing`` Condition. A 1ms blocking read is carried
out before ``done_writing`` is released.

The write thread blocks for 5ms on a queue (to allow the thread to stop). If
a message was received it *sets* the writing_event to tell the read thread
that a message in waiting to be sent. The ``done_writing`` is acquired for
the actual write, the writing_event is cleared and the ``done_writing`` event
is notified to start the read thread again.

.. warning:: Any objects inheriting from `Bus`_ should *not* directly
        use the interface handle(/s).


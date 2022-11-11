.. _kvaserdoc:

Kvaser's CANLIB
===============

`Kvaser <http://www.kvaser.com>`__'s CANLib SDK for Windows (also available on
Linux).

Bus
---

.. autoclass:: can.interfaces.kvaser.canlib.KvaserBus
    :members:
    :exclude-members: get_stats


Internals
---------

The Kvaser :class:`~can.Bus` object with a physical CAN Bus can be operated in two
modes; ``single_handle`` mode with one shared bus handle used for both reading and
writing to the CAN bus, or with two separate bus handles.
Two separate handles are needed if receiving and sending messages are done in
different threads (see `Kvaser documentation
<http://www.kvaser.com/canlib-webhelp/page_user_guide_threads_applications.html>`_).


.. warning:: Any objects inheriting from `Bus`_ should *not* directly
        use the interface handle(/s).


Message filtering
~~~~~~~~~~~~~~~~~

The Kvaser driver and hardware only supports setting one filter per handle.
If one filter is requested, this is will be handled by the Kvaser driver.
If more than one filter is needed, these will be handled in Python code
in the ``recv`` method. If a message does not match any of the filters,
``recv()`` will return None.


Custom methods
~~~~~~~~~~~~~~~~~

This section contains Kvaser driver specific methods.


.. automethod:: can.interfaces.kvaser.canlib.KvaserBus.get_stats

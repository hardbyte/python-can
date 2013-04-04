Library API
===========

The main two objects are the :class:`~can.Bus` and the :class:`~can.Message`.

.. toctree::
   :maxdepth: 1
   
   bus
   message


Listener
--------

The Listener class is an "abstract" class (such that Python has that concept)
which forms the base class for any objects which wish to register to receive
notifications of new messages on the bus. It provides a single method
(on_message_received), which takes a single parameter (the message received
from the bus), and is called by the CAN.Bus object(s) that the Listener is
registered with whenever they receive a new message. Subclasses of Listener
that do not override this method (that is, implement an on_message_received
of their own without calling CAN.Listener's version) will cause
NotImplementedError to be thrown when a message is received on the CAN bus.


BufferedReader
--------------

The BufferedReader class is a subclass of `Listener`_ which implements a
"message buffer": that is, when a BufferedReader instance is notified of a
new message it pushes it into a queue of messages waiting to be serviced.
The BufferedReader class provides a get_message method, which attempts to
retrieve the latest message received by the instance. If no message is
available it blocks for 0.5 seconds or until a message is received (whichever
is shorter), and returns the message if there is one, or None if there is not.


MessagePrinter
--------------

The MessagePrinter class is a subclass of `Listener`_ which simply prints
any messages it receives to the terminal.


AcceptanceFilter
----------------

The AcceptanceFilter class is a subclass of `Listener`_ which implements the
CAN "acceptance filter" rules in software. It in turn has its own list of
listeners, which receive only the messages matching its defined "acceptance
filter" rules.


LogInfo
-------

The LogInfo class provides storage of information about a CAN traffic log,
including data like the time of day at log start and end, the name of the
tester who recorded the log, and the name of the original log file.


Log
----

A Log object contains information about the CAN channel, the machine information
and contains a record of the messages and errors.


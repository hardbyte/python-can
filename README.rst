python-can
==========

|release| |docs| |build_travis| |build_appveyor| |coverage| |downloads|

.. |release| image:: https://img.shields.io/pypi/v/python-can.svg
   :target: https://pypi.python.org/pypi/python-can/
   :alt: Latest Version on PyPi

.. |docs| image:: https://readthedocs.org/projects/python-can/badge/?version=stable
   :target: https://python-can.readthedocs.io/en/stable/
   :alt: Documentation

.. |build_travis| image:: https://img.shields.io/travis/hardbyte/python-can/develop.svg?label=Travis%20CI
   :target: https://travis-ci.org/hardbyte/python-can/branches
   :alt: Travis CI Server for develop branch

.. |build_appveyor| image:: https://img.shields.io/appveyor/ci/hardbyte/python-can/develop.svg?label=AppVeyor
   :target: https://ci.appveyor.com/project/hardbyte/python-can/history
   :alt: AppVeyor CI Server for develop branch

.. |coverage| image:: https://codecov.io/gh/hardbyte/python-can/branch/develop/graph/badge.svg
   :target: https://codecov.io/gh/hardbyte/python-can/branch/develop
   :alt: Test coverage reports on Codecov.io

.. |downloads| image:: https://pepy.tech/badge/python-can
   :target: https://pepy.tech/project/python-can
   :alt: Downloads on PePy

The **C**\ ontroller **A**\ rea **N**\ etwork is a bus standard designed
to allow microcontrollers and devices to communicate with each other. It
has priority based bus arbitration and reliable deterministic
communication. It is used in cars, trucks, boats, wheelchairs and more.

The ``can`` package provides controller area network support for
Python developers; providing common abstractions to
different hardware devices, and a suite of utilities for sending and receiving
messages on a can bus.

The library supports Python 2.7, Python 3.5+ as well as PyPy 2 & 3 and runs on Mac, Linux and Windows.


Features
--------

- common abstractions for CAN communication
- support for many different backends (see the `docs <https://python-can.readthedocs.io/en/stable/interfaces.html>`__)
- receiving, sending, and periodically sending messages
- normal and extended arbitration IDs
- limited `CAN FD <https://en.wikipedia.org/wiki/CAN_FD>`__ support
- many different loggers and readers supporting playback: ASC (CANalyzer format), BLF (Binary Logging Format by Vector), CSV, SQLite and Canutils log
- efficient in-kernel or in-hardware filtering of messages on supported interfaces
- bus configuration reading from file or environment variables
- CLI tools for working with CAN buses (see the `docs <https://python-can.readthedocs.io/en/stable/scripts.html>`__)
- more


Example usage
-------------

.. code:: python

    # import the library
    import can

    # create a bus instance
    # many other interfaces are supported as well (see below)
    bus = can.Bus(interface='socketcan',
                  channel='vcan0',
                  receive_own_messages=True)

    # send a message
    message = can.Message(arbitration_id=123, is_extended_id=True,
                          data=[0x11, 0x22, 0x33])
    bus.send(message, timeout=0.2)

    # iterate over received messages
    for msg in bus:
        print("{X}: {}".format(msg.arbitration_id, msg.data))

    # or use an asynchronous notifier
    notifier = can.Notifier(bus, [can.Logger("recorded.log"), can.Printer()])

You can find more information in the documentation, online at
`python-can.readthedocs.org <https://python-can.readthedocs.org/en/stable/>`__.


Discussion
----------

If you run into bugs, you can file them in our
`issue tracker <https://github.com/hardbyte/python-can/issues>`__ on GitHub.

There is also a `python-can <https://groups.google.com/forum/#!forum/python-can>`__
mailing list for development discussion.

`Stackoverflow <https://stackoverflow.com/questions/tagged/can+python>`__ has several
questions and answers tagged with ``python+can``.

Wherever we interact, we strive to follow the
`Python Community Code of Conduct <https://www.python.org/psf/codeofconduct/>`__.


Contributing
------------

See `doc/development.rst <doc/development.rst>`__ for getting started.

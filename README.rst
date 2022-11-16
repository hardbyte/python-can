python-can
==========

|release| |python_implementation| |downloads| |downloads_monthly| |formatter|

|docs| |github-actions| |build_travis| |coverage| |mergify|

.. |release| image:: https://img.shields.io/pypi/v/python-can.svg
   :target: https://pypi.python.org/pypi/python-can/
   :alt: Latest Version on PyPi

.. |python_implementation| image:: https://img.shields.io/pypi/implementation/python-can
   :target: https://pypi.python.org/pypi/python-can/
   :alt: Supported Python implementations

.. |downloads| image:: https://pepy.tech/badge/python-can
   :target: https://pepy.tech/project/python-can
   :alt: Downloads on PePy

.. |downloads_monthly| image:: https://pepy.tech/badge/python-can/month
   :target: https://pepy.tech/project/python-can
   :alt: Monthly downloads on PePy

.. |formatter| image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/python/black
   :alt: This project uses the black formatter.

.. |docs| image:: https://readthedocs.org/projects/python-can/badge/?version=stable
   :target: https://python-can.readthedocs.io/en/stable/
   :alt: Documentation

.. |github-actions| image:: https://github.com/hardbyte/python-can/actions/workflows/build.yml/badge.svg?branch=develop
   :target: https://github.com/hardbyte/python-can/actions/workflows/build.yml
   :alt: Github Actions workflow status

.. |build_travis| image:: https://img.shields.io/travis/hardbyte/python-can/develop.svg?label=Travis%20CI
   :target: https://app.travis-ci.com/github/hardbyte/python-can
   :alt: Travis CI Server for develop branch

.. |coverage| image:: https://coveralls.io/repos/github/hardbyte/python-can/badge.svg?branch=develop
   :target: https://coveralls.io/github/hardbyte/python-can?branch=develop
   :alt: Test coverage reports on Coveralls.io

.. |mergify| image:: https://img.shields.io/endpoint.svg?url=https://api.mergify.com/v1/badges/hardbyte/python-can&style=flat
   :target: https://mergify.io
   :alt: Mergify Status

The **C**\ ontroller **A**\ rea **N**\ etwork is a bus standard designed
to allow microcontrollers and devices to communicate with each other. It
has priority based bus arbitration and reliable deterministic
communication. It is used in cars, trucks, boats, wheelchairs and more.

The ``can`` package provides controller area network support for
Python developers; providing common abstractions to
different hardware devices, and a suite of utilities for sending and receiving
messages on a can bus.

The library currently supports CPython as well as PyPy and runs on Mac, Linux and Windows.

==============================  ===========
Library Version                 Python
------------------------------  -----------
  2.x                           2.6+, 3.4+
  3.x                           2.7+, 3.5+
  4.x                           3.7+
==============================  ===========


Features
--------

- common abstractions for CAN communication
- support for many different backends (see the `docs <https://python-can.readthedocs.io/en/stable/interfaces.html>`__)
- receiving, sending, and periodically sending messages
- normal and extended arbitration IDs
- `CAN FD <https://en.wikipedia.org/wiki/CAN_FD>`__ support
- many different loggers and readers supporting playback: ASC (CANalyzer format), BLF (Binary Logging Format by Vector), TRC, CSV, SQLite, and Canutils log
- efficient in-kernel or in-hardware filtering of messages on supported interfaces
- bus configuration reading from a file or from environment variables
- command line tools for working with CAN buses (see the `docs <https://python-can.readthedocs.io/en/stable/scripts.html>`__)
- more


Example usage
-------------

``pip install python-can``

.. code:: python

    # import the library
    import can

    # create a bus instance
    # many other interfaces are supported as well (see documentation)
    bus = can.Bus(interface='socketcan',
                  channel='vcan0',
                  receive_own_messages=True)

    # send a message
    message = can.Message(arbitration_id=123, is_extended_id=True,
                          data=[0x11, 0x22, 0x33])
    bus.send(message, timeout=0.2)

    # iterate over received messages
    for msg in bus:
        print(f"{msg.arbitration_id:X}: {msg.data}")

    # or use an asynchronous notifier
    notifier = can.Notifier(bus, [can.Logger("recorded.log"), can.Printer()])

You can find more information in the documentation, online at
`python-can.readthedocs.org <https://python-can.readthedocs.org/en/stable/>`__.


Discussion
----------

If you run into bugs, you can file them in our
`issue tracker <https://github.com/hardbyte/python-can/issues>`__ on GitHub.

`Stackoverflow <https://stackoverflow.com/questions/tagged/can+python>`__ has several
questions and answers tagged with ``python+can``.

Wherever we interact, we strive to follow the
`Python Community Code of Conduct <https://www.python.org/psf/codeofconduct/>`__.


Contributing
------------

See `doc/development.rst <doc/development.rst>`__ for getting started.

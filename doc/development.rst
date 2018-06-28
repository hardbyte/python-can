Developer's Overview
====================


Contributing
------------

Contribute to source code, documentation, examples and report issues:
https://github.com/hardbyte/python-can

There is also a `python-can <https://groups.google.com/forum/#!forum/python-can>`__
mailing list for development discussion.


Building & Installing
---------------------

The following assumes that the commands are executed from the root of the repository:

- The project can be built and installed with ``python setup.py build`` and
  ``python setup.py install``.
- The unit tests can be run with ``python setup.py test``. The tests can be run with ``python2``,
  ``python3``, ``pypy`` or ``pypy3`` to test with other python versions, if they are installed.
  Maybe, you need to execute ``pip3 install python-can[test]`` (or only ``pip`` for Python 2),
  if some dependencies are missing.
- The docs can be built with ``sphinx-build doc/ doc/_build``. Appending ``-n`` to the command
  makes Sphinx complain about more subtle problems.


Creating a new interface/backend
--------------------------------

These steps are a guideline on how to add a new backend to python-can.

- Create a module (either a ``*.py`` or an entire subdirctory depending
  on the complexity) inside ``can.interfaces``
- Implement the central part of the backend: the bus class that extends
  :class:`can.BusABC`. See below for more info on this one!
- Register your backend bus class in ``can.interface.BACKENDS`` and
  ``can.interfaces.VALID_INTERFACES``.
- Add docs where appropiate, like in ``doc/interfaces.rst`` and add
  an entry in ``doc/interface/*``.
- Add tests in ``test/*`` where appropiate.

About the ``BusABC`` class
==========================

Concrete implementations *have to* implement the following:
    * :meth:`~can.BusABC.send` to send individual messages
    * :meth:`~can.BusABC._recv_internal` to receive individual messages
      (see note below!)
    * set the :attr:`~can.BusABC.channel_info` attribute to a string describing
      the underlying bus and/or channel

They *might* implement the following:
    * :meth:`~can.BusABC.flush_tx_buffer` to allow discrading any
      messages yet to be sent
    * :meth:`~can.BusABC.shutdown` to override how the bus should
      shut down
    * :meth:`~can.BusABC.send_periodic` to override the software based
      periodic sending and push it down to the kernel or hardware
    * :meth:`~can.BusABC._apply_filters` to apply efficient filters
      to lower level systems like the OS kernel or hardware
    * :meth:`~can.BusABC._detect_available_configs` to allow the interface
      to report which configurations are currently available for new
      connections
    * :meth:`~can.BusABC.state` property to allow reading and/or changing
      the bus state

.. note::

    *TL;DR*: Only override :meth:`~can.BusABC._recv_internal`,
    never :meth:`~can.BusABC.recv` directly.

    Previously, concrete bus classes had to override :meth:`~can.BusABC.recv`
    directly instead of :meth:`~can.BusABC._recv_internal`, but that has
    changed to allow the abstract base class to handle in-software message
    filtering as a fallback. All internal interfaces now implement that new
    behaviour. Older (custom) interfaces might still be implemented like that
    and thus might not provide message filtering:


Code Structure
--------------

The modules in ``python-can`` are:

+---------------------------------+------------------------------------------------------+
|Module                           | Description                                          |
+=================================+======================================================+
|:doc:`interfaces <interfaces>`   | Contains interface dependent code.                   |
+---------------------------------+------------------------------------------------------+
|:doc:`bus <bus>`                 | Contains the interface independent Bus object.       |
+---------------------------------+------------------------------------------------------+
|:doc:`message <message>`         | Contains the interface independent Message object.   |
+---------------------------------+------------------------------------------------------+
|:doc:`io <listeners>`            | Contains a range of file readers and writers.        |
+---------------------------------+------------------------------------------------------+
|:doc:`broadcastmanager <bcm>`    | Contains interface independent broadcast manager     |
|                                 | code.                                                |
+---------------------------------+------------------------------------------------------+
|:doc:`CAN <api>`                 | Legacy API. Deprecated.                              |
+---------------------------------+------------------------------------------------------+


Creating a new Release
----------------------

- Release from the ``master`` branch.
- Update the library version in ``__init__.py`` using `semantic versioning <http://semver.org>`__.
- Run all tests and examples against available hardware.
- Update `CONTRIBUTORS.txt` with any new contributors.
- For larger changes update ``doc/history.rst``.
- Sanity check that documentation has stayed inline with code.
- Create a temporary virtual environment. Run ``python setup.py install`` and ``python setup.py test``
- Create and upload the distribution: ``python setup.py sdist bdist_wheel``
- Sign the packages with gpg ``gpg --detach-sign -a dist/python_can-X.Y.Z-py3-none-any.whl``
- Upload with twine ``twine upload dist/python-can-X.Y.Z*``
- In a new virtual env check that the package can be installed with pip: ``pip install python-can==X.Y.Z``
- Create a new tag in the repository.
- Check the release on PyPi, Read the Docs and GitHub.

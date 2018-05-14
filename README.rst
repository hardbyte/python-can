python-can
==========

|release| |docs| |build_travis| |build_appveyor|

.. |release| image:: https://img.shields.io/pypi/v/python-can.svg
   :target: https://pypi.python.org/pypi/python-can/
   :alt: Latest Version on PyPi

.. |docs| image:: https://readthedocs.org/projects/python-can/badge/?version=stable
   :target: https://python-can.readthedocs.io/en/stable/
   :alt: Documentation build Status
                
.. |build_travis| image:: https://travis-ci.org/hardbyte/python-can.svg?branch=develop
   :target: https://travis-ci.org/hardbyte/python-can/branches
   :alt: Travis CI Server for develop branch

.. |build_appveyor| image:: https://ci.appveyor.com/api/projects/status/github/hardbyte/python-can?branch=develop&svg=true
   :target: https://ci.appveyor.com/project/hardbyte/python-can/history
   :alt: AppVeyor CI Server for develop branch


The **C**\ ontroller **A**\ rea **N**\ etwork is a bus standard designed
to allow microcontrollers and devices to communicate with each other. It
has priority based bus arbitration, reliable deterministic
communication. It is used in cars, trucks, boats, wheelchairs and more.

The ``can`` package provides controller area network support for
Python developers; providing `common abstractions to
different hardware devices`, and a suite of utilities for sending and receiving
messages on a can bus.

The library supports Python 2.7, Python 3.4+ as well as PyPy 2 & 3 and runs on Mac, Linux and Windows.

You can find more information in the documentation, online at
`python-can.readthedocs.org <https://python-can.readthedocs.org/en/stable/>`__.


Discussion
----------

If you run into bugs, you can file them in our
`issue tracker <https://github.com/hardbyte/python-can/issues>`__.

There is also a `python-can <https://groups.google.com/forum/#!forum/python-can>`__
mailing list for development discussion.

`Stackoverflow <https://stackoverflow.com/questions/tagged/can+python>`__ has several
questions and answers tagged with ``python+can``.

Wherever we interact, we strive to follow the
`Python Community Code of Conduct <https://www.python.org/psf/codeofconduct/>`__.

Contributing
------------

See `doc/development.rst <doc/development.rst>`__ for getting started.

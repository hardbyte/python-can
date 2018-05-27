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
|:doc:`CAN <api>`                 | Legacy API. Depecated.                               |
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
- Check the release on PyPi, Read the docs and GitHub.

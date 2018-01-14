Developer's Overview
====================


Contributing
------------

Contribute to source code, documentation, examples and report issues:
https://github.com/hardbyte/python-can


Building & Installing
---------------------

This assumes that the commands are executed from the root of the repository:

- The project can be built and installed with ``python setup.py build`` and
``python setup.py install``.
- The unit tests can be run with ``python setup.py test``. The tests can be run with `python2` and `python3` to check with both major python versions, if they are installed.
- The docs can be built with ``sphinx-build doc/ doc/_build``.


Creating a Release
------------------

- Release from the ``master`` branch.
- Update the library version in ``__init__.py`` using `semantic versioning <http://semver.org>`__.
- Run all tests and examples against available hardware.
- Update `CONTRIBUTORS.txt` with any new contributors.
- Sanity check that documentation has stayed inline with code. For large changes update ``doc/history.rst``
- Create a temporary virtual environment. Run ``python setup.py install`` and ``python setup.py test``
- Create and upload the distribution: ``python setup.py sdist bdist_wheel``
- Sign the packages with gpg ``gpg --detach-sign -a dist/python_can-X.Y.Z-py3-none-any.whl``
- Upload with twine ``twine upload dist/python-can-X.Y.Z*``
- In a new virtual env check that the package can be installed with pip: ``pip install python-can==X.Y.Z``
- Create a new tag in the repository.
- Check the release on PyPi and github.


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
|:doc:`CAN <api>`                 | Contains modules to emulate a CAN system, such as a  |
|                                 | time stamps, read/write streams and listeners.       |
+---------------------------------+------------------------------------------------------+
|:doc:`message <message>`         | Contains the interface independent Message object.   |
+---------------------------------+------------------------------------------------------+
|:doc:`notifier <api>`            | An object which can be used to notify listeners.     |
+---------------------------------+------------------------------------------------------+
|:doc:`broadcastmanager <bcm>`    | Contains interface independent broadcast manager     |
|                                 | code.                                                |
+---------------------------------+------------------------------------------------------+

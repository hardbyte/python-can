Developer's Overview
====================


Contributing
------------

Contribute to source code, documentation, examples and report issues:
https://github.com/hardbyte/python-can

Note that the latest released version on PyPi may be significantly behind the
``develop`` branch. Please open any feature requests against the ``develop`` branch

There is also a `python-can <https://groups.google.com/forum/#!forum/python-can>`__
mailing list for development discussion.

Some more information about the internals of this library can be found
in the chapter :ref:`internalapi`.
There is also additional information on extending the ``can.io`` module.


Pre-releases
------------

The latest pre-release can be installed with::

    pip install --upgrade --pre python-can



Building & Installing
---------------------

The following assumes that the commands are executed from the root of the repository:

The project can be built with::

    pipx run build
    pipx run twine check dist/*

The project can be installed in editable mode with::

    pip install -e .

The unit tests can be run with::

    pipx run tox -e py

The documentation can be built with::

    pip install -r doc/doc-requirements.txt
    python -m sphinx -an doc build

The linters can be run with::

    pip install -r requirements-lint.txt
    pylint --rcfile=.pylintrc-wip can/**.py
    black --check --verbose can


Creating a new interface/backend
--------------------------------

These steps are a guideline on how to add a new backend to python-can.

- Create a module (either a ``*.py`` or an entire subdirectory depending
  on the complexity) inside ``can.interfaces``
- Implement the central part of the backend: the bus class that extends
  :class:`can.BusABC`.
  See :ref:`businternals` for more info on this one!
- Register your backend bus class in ``BACKENDS`` in the file ``can.interfaces.__init__.py``.
- Add docs where appropriate. At a minimum add to ``doc/interfaces.rst`` and add
  a new interface specific document in ``doc/interface/*``.
  It should document the supported platforms and also the hardware/software it requires.
  A small snippet of how to install the dependencies would also be useful to get people started without much friction.
- Also, don't forget to document your classes, methods and function with docstrings.
- Add tests in ``test/*`` where appropriate.
  To get started, have a look at ``back2back_test.py``:
  Simply add a test case like ``BasicTestSocketCan`` and some basic tests will be executed for the new interface.

.. attention::
    We strongly recommend using the :ref:`plugin interface` to extend python-can.
    Publish a python package that contains your :class:`can.BusABC` subclass and use
    it within the python-can API. We will mention your package inside this documentation
    and add it as an optional dependency.

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


Creating a new Release
----------------------

- Release from the ``main`` branch (except for pre-releases).
- Update the library version in ``__init__.py`` using `semantic versioning <http://semver.org>`__.
- Check if any deprecations are pending.
- Run all tests and examples against available hardware.
- Update ``CONTRIBUTORS.txt`` with any new contributors.
- For larger changes update ``doc/history.rst``.
- Sanity check that documentation has stayed inline with code.
- Create a temporary virtual environment. Run ``python setup.py install`` and ``tox``.
- Create and upload the distribution: ``python setup.py sdist bdist_wheel``.
- Sign the packages with gpg ``gpg --detach-sign -a dist/python_can-X.Y.Z-py3-none-any.whl``.
- Upload with twine ``twine upload dist/python-can-X.Y.Z*``.
- In a new virtual env check that the package can be installed with pip: ``pip install python-can==X.Y.Z``.
- Create a new tag in the repository.
- Check the release on
  `PyPi <https://pypi.org/project/python-can/#history>`__,
  `Read the Docs <https://readthedocs.org/projects/python-can/versions/>`__ and
  `GitHub <https://github.com/hardbyte/python-can/releases>`__.

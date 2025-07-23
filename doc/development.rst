Developer's Overview
====================

Quick Start for Contributors
----------------------------
* Fork the repository on GitHub and clone your fork.
* Create a new branch for your changes.
* Set up your development environment.
* Make your changes, add/update tests and documentation as needed.
* Run `tox` to check your changes.
* Push your branch and open a pull request.

Contributing
------------

Welcome! Thank you for your interest in python-can. Whether you want to fix a bug,
add a feature, improve documentation, write examples, help solve issues,
or simply report a problem, your contribution is valued.
Contributions are made via the `python-can GitHub repository <https://github.com/hardbyte/python-can>`_.
If you have questions, feel free to open an issue or start a discussion on GitHub.

If you're new to the codebase, see the next section for an overview of the code structure.
For more about the internals, see :ref:`internalapi` and information on extending the ``can.io`` module.

Code Structure
^^^^^^^^^^^^^^

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
|:doc:`io <file_io>`              | Contains a range of file readers and writers.        |
+---------------------------------+------------------------------------------------------+
|:doc:`broadcastmanager <bcm>`    | Contains interface independent broadcast manager     |
|                                 | code.                                                |
+---------------------------------+------------------------------------------------------+

Step-by-Step Contribution Guide
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. **Fork and Clone the Repository**

   * Fork the python-can repository on GitHub to your own account.
   * Clone your fork:

     .. code-block:: shell

        git clone https://github.com/<your-username>/python-can.git
        cd python-can

   * Create a new branch for your work:

     .. code-block:: shell

        git checkout -b my-feature-branch

   * Ensure your branch is up to date with the latest changes from the main repository. 
     First, add the main repository as a remote (commonly named `upstream`) if you haven't already:

     .. code-block:: shell

        git remote add upstream https://github.com/hardbyte/python-can.git

     Then, regularly fetch and rebase from the main branch:

     .. code-block:: shell

        git fetch upstream
        git rebase upstream/main

2. **Set Up Your Development Environment**

   You can use either `pipx <https://pipx.pypa.io/>`__ or `uv <https://docs.astral.sh/uv/>`__ 
   to install development tools. Both methods are supported:

   * **pipx** is a tool for installing and running Python applications (such as tox) 
     in isolated environments, separate from your global Python installation. 
     It is useful for globally installing CLI tools without affecting your project's dependencies or environment.
   * **uv** is a modern Python packaging tool that can quickly create virtual environments and manage dependencies, 
     including downloading required Python versions automatically. 
     The `uvx` command also provides functionality similar to pipx, 
     allowing you to run CLI tools in isolated environments.

   Choose the method that best fits your workflow and system setup.

   **Install tox (if not already available):**

   .. tab:: Using uv

     .. code-block:: shell

        uv tool install tox --with tox-uv

   .. tab:: Using pipx

     .. code-block:: shell

        pipx install tox

   **Create a virtual environment and install python-can in editable mode**

   .. tab:: Using uv

      .. code-block:: shell

         uv venv
         .venv\Scripts\activate  # On Windows
         source .venv/bin/activate  # On Unix/macOS
         uv pip install -e . --group dev

   .. tab:: Using virtualenv and pip

      .. code-block:: shell

         python -m venv .venv
         .venv\Scripts\activate  # On Windows
         source .venv/bin/activate  # On Unix/macOS
         python -m pip install --upgrade pip
         pip install -e . --group dev

3. **Make Your Changes**

   * Edit code, documentation, or tests as needed.
   * If you fix a bug or add a feature, add or update tests in the ``test/`` directory.
   * If your change affects users, update documentation in ``doc/`` and relevant docstrings.

4. **Test Your Changes**

   This project uses `tox <https://tox.wiki/en/latest/>`__ to automate all checks (tests, lint, type, docs). 
   Tox will set up isolated environments and run the right tools for you.

   To run all checks:

   .. code-block:: shell

      tox

   To run a specific check, use:

   .. code-block:: shell

      tox -e lint      # Run code style and lint checks (black, ruff, pylint)
      tox -e type      # Run type checks (mypy)
      tox -e docs      # Build and test documentation (sphinx)
      tox -e py        # Run tests (pytest)

   To run all checks in parallel (where supported), you can use:

   .. code-block:: shell

      tox p

   Some environments require specific Python versions. 
   If you use `uv`, it will automatically download and manage these for you. 
   With `pipx`, you may need to install the required Python versions yourself.

5. **(Optional) Build Source Distribution and Wheels**

   If you want to manually build the source distribution (sdist) and wheels for python-can, 
   you can use either `uvx` or `pipx` to run the build and twine tools. 
   Choose the method that best fits your workflow.

   .. tab:: Using uvx

      .. code-block:: shell

         uvx --from build pyproject-build --installer uv
         uvx twine check --strict dist/*

   .. tab:: Using pipx

      .. code-block:: shell

         pipx run build
         pipx run twine check dist/*

6. **Push and Submit Your Contribution**

   * Push your branch:

     .. code-block:: shell

        git push origin my-feature-branch

   * Open a pull request from your branch to the ``main`` branch of the main python-can repository on GitHub.

   Please be patient — maintainers review contributions as time allows.

Creating a new interface/backend
--------------------------------

.. attention::
    We strongly recommend using the :ref:`plugin interface` to extend python-can.
    Publish a python package that contains your :class:`can.BusABC` subclass and use
    it within the python-can API. We will mention your package inside this documentation
    and add it as an optional dependency.

These steps are a guideline on how to add a new backend to python-can.

* Create a module (either a ``*.py`` or an entire subdirectory depending
  on the complexity) inside ``can.interfaces``. See ``can/interfaces/socketcan`` for a reference implementation.
* Implement the central part of the backend: the bus class that extends
  :class:`can.BusABC`.
  See :ref:`businternals` for more info on this one!
* Register your backend bus class in ``BACKENDS`` in the file ``can.interfaces.__init__.py``.
* Add docs where appropriate. At a minimum add to ``doc/interfaces.rst`` and add
  a new interface specific document in ``doc/interface/*``.
  It should document the supported platforms and also the hardware/software it requires.
  A small snippet of how to install the dependencies would also be useful to get people started without much friction.
* Also, don't forget to document your classes, methods and function with docstrings.
* Add tests in ``test/*`` where appropriate. For example, see ``test/back2back_test.py`` and add a test case like ``BasicTestSocketCan`` for your new interface.

Creating a new Release
----------------------

* Releases are automated via GitHub Actions. To create a new release:

  * Ensure all tests pass and documentation is up-to-date.
  * Update ``CONTRIBUTORS.txt`` with any new contributors.
  * For larger changes, update ``doc/history.rst``.
  * Create a new tag and GitHub release (e.g., ``vX.Y.Z``) targeting the ``main`` branch. Add release notes and publish.
  * The CI workflow will automatically build, check, and upload the release to PyPI and other platforms.

* You can monitor the release status on:
  `PyPi <https://pypi.org/project/python-can/#history>`__,
  `Read the Docs <https://readthedocs.org/projects/python-can/versions/>`__ and
  `GitHub Releases <https://github.com/hardbyte/python-can/releases>`__.

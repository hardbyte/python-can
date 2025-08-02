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

   We recommend using `uv <https://docs.astral.sh/uv/>`__ to install development tools and run CLI utilities.
   `uv` is a modern Python packaging tool that can quickly create virtual environments and manage dependencies,
   including downloading required Python versions automatically. The `uvx` command allows you to run CLI tools
   in isolated environments, separate from your global Python installation. This is useful for installing and
   running Python applications (such as tox) without affecting your project's dependencies or environment.

   **Install tox (if not already available):**


   .. code-block:: shell

      uv tool install tox --with tox-uv


   **Quickly running your local python-can code**

   To run a local script (e.g., `snippet.py`) using your current python-can code,
   you can use either the traditional `virtualenv` and `pip` workflow or the modern `uv` tool.

   **Traditional method (virtualenv + pip):**

   Create a virtual environment and install the package in editable mode.
   This allows changes to your local code to be reflected immediately, without reinstalling.

   .. code-block:: shell

      # Create a new virtual environment
      python -m venv .venv

      # Activate the environment
      .venv\Scripts\activate    # On Windows
      source .venv/bin/activate  # On Unix/macOS

      # Upgrade pip and install python-can in editable mode with development dependencies
      python -m pip install --upgrade pip
      pip install -e .[dev]

      # Run your script
      python snippet.py

   **Modern method (uv):**

   With `uv`, you can run your script directly:

   .. code-block:: shell

      uv run snippet.py

   When ``uv run ...`` is called inside a project, 
   `uv` automatically sets up the environment and symlinks local packages. 
   No editable install is needed—changes to your code are reflected immediately.

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



5. **Add a News Fragment for the Changelog**

   This project uses `towncrier <https://towncrier.readthedocs.io/>`__ to manage the changelog in
   ``CHANGELOG.md``. For every user-facing change (new feature, bugfix, deprecation, etc.), you
   must add a news fragment:
   
   * News fragments are short files describing your change, stored in ``doc/changelog.d``.
   * Name each fragment ``<issue-or-description>.<type>.md``, where ``<type>`` is one of:
     ``added``, ``changed``, ``deprecated``, ``removed``, ``fixed``, or ``security``.
   * Example (for a feature added in PR #1234):
   
     .. code-block:: shell
   
        echo "Added support for CAN FD." > doc/changelog.d/1234.added.md
   
   * Or use the towncrier CLI:
   
     .. code-block:: shell
   
        uvx towncrier create --dir doc/changelog.d -c "Added support for CAN FD." 1234.added.md
   
   * For changes not tied to an issue/PR, the fragment name must start with a plus symbol
     (e.g., ``+mychange.added.md``). Towncrier calls these "orphan fragments".
   
   .. note:: You do not need to manually update ``CHANGELOG.md``—maintainers will build the
             changelog at release time.

6. **(Optional) Build Source Distribution and Wheels**

   If you want to manually build the source distribution (sdist) and wheels for python-can,
   you can use `uvx` to run the build and twine tools:

   .. code-block:: shell

      uv build
      uvx twine check --strict dist/*

7. **Push and Submit Your Contribution**

   * Push your branch:

     .. code-block:: shell

        git push origin my-feature-branch

   * Open a pull request from your branch to the ``main`` branch of the main python-can repository on GitHub.

   Please be patient — maintainers review contributions as time allows.

Creating a new interface/backend
--------------------------------

.. attention::
   Please note: Pull requests that attempt to add new hardware interfaces directly to the
   python-can codebase will not be accepted. Instead, we encourage contributors to create
   plugins by publishing a Python package containing your :class:`can.BusABC` subclass and
   using it within the python-can API. We will mention your package in this documentation
   and add it as an optional dependency. For current best practices, please refer to
   :ref:`plugin interface`.

   The following guideline is retained for informational purposes only and is not valid for new
   contributions.

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

Releases are automated via GitHub Actions. To create a new release:

* Build the changelog with towncrier:


  * Collect all news fragments and update ``CHANGELOG.md`` by running:

    .. code-block:: shell

       uvx towncrier build --yes --version vX.Y.Z

    (Replace ``vX.Y.Z`` with the new version number. **The version must exactly match the tag you will create for the release.**)
    This will add all news fragments to the changelog and remove the fragments by default.

    .. note:: You can generate the changelog for prereleases, but keep the news
              fragments so they are included in the final release. To do this, replace ``--yes`` with ``--keep``.
              This will update ``CHANGELOG.md`` but leave the fragments in place for future builds.
   
  * Review ``CHANGELOG.md`` for accuracy and completeness.

* Ensure all tests pass and documentation is up-to-date.
* Update ``CONTRIBUTORS.txt`` with any new contributors.
* For larger changes, update ``doc/history.rst``.
* Create a new tag and GitHub release (e.g., ``vX.Y.Z``) targeting the ``main``
  branch. Add release notes and publish.
* The CI workflow will automatically build, check, and upload the release to PyPI
  and other platforms.

* You can monitor the release status on:
  `PyPi <https://pypi.org/project/python-can/#history>`__,
  `Read the Docs <https://readthedocs.org/projects/python-can/versions/>`__ and
  `GitHub Releases <https://github.com/hardbyte/python-can/releases>`__.

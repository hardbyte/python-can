python-can
==========

`python-can` is a library for interacting with a controller area network.

The **Controller Area Network** is a bus standard designed to allow embedded
devices to communicate with each other. It has priority based bus arbitration,
reliable deterministic communication. It is used in cars, trucks, boats,
wheelchairs and more.


Contents:

.. toctree::
   :maxdepth: 2

   interfaces
   api
   protocols
   bin
   overview
   history


Example
~~~~~~~

This example shows the library in action - sending one message:


.. literalinclude:: ../examples/send_one.py
    :language: python
    :linenos:



Installation and Quickstart
~~~~~~~~~~~~~~~~~~~~~~~~~~~

See the readme included with the source code.

https://bitbucket.org/hardbyte/python-can

Known Bugs
~~~~~~~~~~

See the project `bug tracker`_ on bitbucket. Patches and pull requests very welcome!


.. admonition:: Documentation generated

    |today|


.. _Python: http://www.python.org
.. _Setuptools: http://pypi.python.org/pypi/setuptools
.. _Pip: http://pip.openplans.org/
.. _easy_install: http://peak.telecommunity.com/DevCenter/EasyInstall
.. _IPython: http://ipython.scipy.org
.. _Mercurial: http://mercurial.selenic.com
.. _TortoiseHG: http://tortoisehg.bitbucket.org/
.. _bug tracker: https://bitbucket.org/hardbyte/python-can/issues
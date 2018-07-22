python-can
==========


The **python-can** library provides Controller Area Network support for
`Python <http://python.org/download/>`__, providing common abstractions to
different hardware devices, and a suite of utilities for sending and receiving
messages on a CAN bus.

**python-can** runs any where Python runs; from high powered computers
with commercial `CAN to usb` devices right down to low powered devices running
linux such as a BeagleBone or RaspberryPi.

More concretely, some example uses of the library:

- Passively logging what occurs on a CAN bus. For example monitoring a
  commercial vehicle using its **OBD-II** port.

- Testing of hardware that interacts via CAN. Modules found in
  modern cars, motocycles, boats, and even wheelchairs have had components tested
  from Python using this library.

- Prototyping new hardware modules or software algorithms in-the-loop. Easily
  interact with an existing bus.

- Creating virtual modules to prototype CAN bus communication.


Brief example of the library in action: connecting to a CAN bus, creating and sending a message:


.. literalinclude:: ../examples/send_one.py
    :language: python
    :linenos:


Contents:

.. toctree::
   :maxdepth: 2

   installation
   configuration
   api
   interfaces
   scripts
   development
   history


Known Bugs
~~~~~~~~~~

See the project `bug tracker`_ on github. Patches and pull requests very welcome!


.. admonition:: Documentation generated

    |today|


.. _Python: http://www.python.org
.. _Setuptools: http://pypi.python.org/pypi/setuptools
.. _Pip: http://pip.openplans.org/
.. _easy_install: http://peak.telecommunity.com/DevCenter/EasyInstall
.. _IPython: http://ipython.scipy.org
.. _bug tracker: https://github.com/hardbyte/python-can/issues

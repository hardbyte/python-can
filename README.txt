Installation
============

A Controller Area Networking interface is required for `python-can` to do
anything useful. The two primary interfaces are `socketcan` on GNU/Linux 
and Kvaser's CANLib SDK for Windows (and Linux).

The interface is selected at install time with a configuration script.

You can choose which backends to enable by setting the flags in setup.cfg, but
the default is to automatically detect your installed interfaces and build 
support for them.  

.. warning:: 
	If you later find that you did not have an interface installed when you 
	built python-can, but now want it, you will need to install the interface
	and rebuild.


GNU/Linux dependencies
----------------------

Reasonably modern Linux Kernels (3.2+) have an implementation of ``socketcan``.
This version of python-can uses that interface via ctypes.

.. todo::
    Are there any dependencies for linux?

Windows dependencies
--------------------

To install `python-can` using the Kvaser CANLib SDK as the backend:

#. Install Python 2.x

    `Python Downloads <http://python.org/download/>`_.

#. Install Kvaser's CANLib

    Download and install the Windows Kvaser drivers from
    `Download page <http://www.kvaser.com/en/downloads.html>`_.
 

.. note:: 
    Test that Kvaser's own tools work!


Install python-can
-------------------

Two options, install normally with:

    ``python setup.py install``

Or to do a "development" install of this package to your machine (this allows 
you to pull later updates of the source from the Mercurial repository and
use them without having to reinstall). Note that the cloned repo should 
*not* be deleted after this step!:

    ``python setup.py develop``

.. note::
    On linux you will probably need sudo rights. 


Generating Documentation
------------------------

The documentation for python-can has been generated with Sphinx. 

With sphinx installed the documentation can be generated with

    ``python setup.py build_sphinx``

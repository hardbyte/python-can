Installation
--------------------

This document assumes a workstation set up for development using Mercurial
(i.e. Mercurial installed and set up correctly, with an SSH key for the user
doing the install). Python 2.6 or later must be installed as well.


.. warning::

    Sorry there is **no socketcan support on windows**! All instructions
    below are for linux users.

1. Install Leaf Kernel Module
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Make sure your system is set up for kernel compilation, and has header
   packages installed.
#. Obtain the leaf kernel module source from:
    hg clone hg.sw/pdixon/leaf-socketcan
#. Do ``sudo make install`` to build and install the drivers.

2. Install Python setuptools
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Do ``sudo aptitude install python-setuptools`` to install setuptools.

3. Install hgversionutils (OPTIONAL) 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Do ``hg clone ssh://hg.sw/user/bpowell/hgversionutils`` to clone the
   hgversionutils source to your machine.
2. Do ``sudo python2.6 setup.py install`` to install this package (the cloned
   repository may be deleted after the package is installed).

3. Install pycanlib-socketcan
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Do ``hg clone ssh://hg.sw/user/rose/pycanlib-socketcan`` to clone the pycanlib
   source to your machine.
2. Do ``sudo python setup.py develop`` to do a "development" install of this
   package to your machine (this allows you to pull later updates of the
   pycanlib source from the Mercurial repo and use them without having to
   reinstall pycanlib). Note that the cloned repo should *not* be deleted after
   this step!

4. Install IPython (OPTIONAL) 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

IPython is an extended command interpreter for Python, offering syntax
colouring and tab-completion, among many other features. The pycanlib package
includes some utilities that can be used to manipulate CAN traffic streams
using the ipython interface.

Do ``sudo aptitude install ipython`` to install IPython.


To check that the install worked, enter ``ipython -p pycanlib`` on the
command line. You should see something like the following::

    Importing ipipe library...
    Importing pycanlib IPython extensions...
            ReadCAN...
            WriteCAN...
            PrintCAN...
            ReadLog...
            WriteLog...
            AcceptanceFilter...
            ExtractTimeslice...

Documentation
-------------

The documentation for pycanlib-socketcan has been generated with Sphinx. 
Sphinx can be installed by running

``sudo apt-get install sphinxbase-utils`` and

``sudo apt-get install python-sphinx``

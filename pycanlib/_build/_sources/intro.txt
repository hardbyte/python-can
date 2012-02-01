Introduction and Installation 
=============================

Background
----------

The pycanlib-leaf library is built upon the leaf-socketcan driver written
by Phil Dixon (pdixon@dynamiccontrols.com). This driver replaces the functionality of the current Kvaser
provided driver and API, libcanlib. The purpose of the switch is to:

*   Utilise SocketCAN, which is part of the standard system utilities of Linux.  
    A lot of other CAN related applications are built upon SocketCAN. 
*   Speed

Currently, CAN messages can be received but not sent. The implementation 
of this functionality needs to be completed in the leaf-socketcan driver
before it can be added at the pycanlib-leaf level. 

pycanlib-leaf is completely compatible with py1939lib and pyunidrivelib. 

For those familiar with pycanlib, the main change to it has been the replacement
of canlib.py with socketcanlib.py. Also InputValidation has been removed.  

Installation
------------

As SocketCAN is necessary for this software, it **will not run on Windows**.

Changing from pycanlib to pycanlib-leaf
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

*   Uninstall libcanlib

*   Obtain Phil's leaf driver. Follow the readme in there. 

    ``hg clone ssh://hg.sw/user/pdixon/leaf-socketcan``
*   Get pycanlib-leaf


Starting from scratch
~~~~~~~~~~~~~~~~~~~~~

If you haven't really set up your computer you should probably do these things:

*   Follow the UniShark Getting Started Guide 
    
    http://unishark.sw/wiki/UniSharkGettingStartedGuide
*   Install Python 2.7 
    
    ``sudo apt-get install python2.7``
*   Install python setup tools

    ``sudo apt-get install python-setuptools``
*   Install Mercurial

    ``sudo apt-get install mercurial``
    
Once your computer's set up you should: 

*   Obtain Phil's leaf driver. Follow the readme in there. 

    ``hg clone ssh://hg.sw/user/pdixon/leaf-socketcan``
*   Get pycanlib-leaf

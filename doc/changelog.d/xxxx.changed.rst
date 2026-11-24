Update PCAN timestamp determination for Linux and Windows, using the Unix
epoch or native Windows system time APIs where available and falling back to
the ``uptime`` package where necessary.

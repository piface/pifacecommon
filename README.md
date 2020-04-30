pifacecommon
============

Common functions for interacting with PiFace products.


Documentation
=============

[http://pifacecommon.readthedocs.org/](http://pifacecommon.readthedocs.org/)

You can also find the documentation installed at:

    /usr/share/doc/python3-pifacecommon/

Install
=======

Make sure you are using the lastest version of Raspbian:

    $ sudo apt-get update
    $ sudo apt-get upgrade

Install `pifacecommon` with the following commands:

    Python 3:
    $ sudo pip3 install pifacecommon

    Notice 1: Installation from Raspbian repository with apt is not longer the preferred way, take a look into [https://github.com/piface/pifacecommon/issues/27#issuecomment-451400154](issue 27)
    
    Notice 2: Python 2 support is "end-of-life" since Jan 2020, refer to https://www.python.org/doc/sunset-python-2/
    

You will also need to set up automatic loading of the SPI kernel module which
can be done with the lastest version of `raspi-config`. Run:

    $ sudo raspi-config

Then navigate to `Advanced Options`, `SPI` and select `yes`.

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

Install `pifacecommon` (for Python 3 and 2) with the following command:

    $ sudo apt-get install python{,3}-pifacecommon

You will also need to set up automatic loading of the SPI kernel module which
can be done with the lastest version of `raspi-config`. Run:

    $ sudo raspi-config

Then navigate to `Advanced Options`, `SPI` and select `yes`.

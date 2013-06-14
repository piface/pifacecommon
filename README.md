pifacecommon
============

Common functions for interacting with PiFace products. Also available from 
[PyPI](https://pypi.python.org/pypi/pifacecommon/)

Auto Installation
=================
### GitHub

    $ git clone https://github.com/piface/pifacecommon.git
    $ cd pifacecommon
    $ sudo ./install.sh

### PyPI
(You will have to set up SPI stuff manually if this is your first time)

    $ sudo easy_install3 pifacecommon

Manual Installation
===================
### 1. Enable the SPI module
PiFace boards communicate with the Raspberry Pi through the SPI interface.
The SPI interface driver is included in the latest Raspbian distributions
but is not enabled by default. You can permanently enable it by running one of 
the helper scripts in this repository (under bin/):

    $ sudo bin/unblacklist-spi-bcm2708.sh

or to load the SPI driver manually, type `$ sudo modprobe spi-bcm2708`. *This will not persist after a reboot*.

After a reboot the /dev/spidev* devices should now appear but they require
special privileges for the user *pi* to access them. You can set these up by
running:

    $ sudo bin/spidev-setup.sh

### 2. Building and installing
Python automatically builds the source, generates the egg file and installs with:

    $ sudo python3 setup.py install

Examples
========

    $ python3
    >>> import pifacecommon
    >>> pifacecommon.init()
    >>> pifacecommon.write(0xAA, pifacecommon.GPIOA)
    >>> pifacecommon.read(pifacecommon.GPIOA)
    0xAA

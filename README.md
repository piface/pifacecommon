pifacecommon
============

Common functions for interacting with PiFace products.

Auto Installation
=================
### Installing the software
    $ sudo ./install.sh

Manual Installation
===================
### 1. Enable the SPI module
The PiFace tools communicate with the Raspberry Pi using the SPI interface.
The SPI interface driver is included in the latest Raspbian distributions
but is not enabled by default.

To load the SPI driver manually, type:

    $ sudo modprobe spi-bcm2708

*This will not persist after a reboot.* To permanently enable the SPI module
comment out the spi module blacklist line in /etc/modprobe.d/raspi-blacklist.conf.
You can do this automatically by running the `unblacklist-spi-bcm2708.sh' script.

After a reboot the /dev/spidev* devices should appear but they require special
privileges to access them. You'll need to add a udev rule (udev monitors and
configures devices) and set up groups by running `spidev-setup.sh'.

### 2. Building and installing
Python automatically builds the source, generates the egg file and installs.

    $ sudo python3 setup.py install

Examples
========

    $ python3
    >>> import pifacecommon
    >>> pifacecommon.init()
    >>> pifacecommon.write(0xAA, pifacecommon.GPIOA)
    >>> pifacecommon.read(pifacecommon.GPIOA)
    0xAA

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

### 2. Building and installing the distribution egg
You'll need to install the Python 3 setup tools.

	$ sudo aptitude install python3-setuptools

A Python egg can be distributed on it's own but for the time being we'll build
one from source and install it using easy_install3.

    $ python3 setup.py bdist_egg
    $ easy_install3 dist/pifacecommon-1.0-py3.2.egg

Alternatively we could have just run `python3 setup.py install' but I'm hoping
to distribute the eggs on their own (in a .deb) soon.
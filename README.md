pifacecommon
============

Common functions for interacting with PiFace products.

Installation
============
### Enabling the SPI module
The PiFace tools communicate with the Raspberry Pi using the SPI interface.
The SPI interface driver is included in the latest Raspbian distributions
but is not enabled by default.

To load the SPI driver manually, type:

    $ sudo modprobe spi-bcm2708

*This will not persist after a reboot.* To permanently enable the SPI module
comment out the spi module blacklist line in /etc/modprobe.d/raspi-blacklist.conf
(you will have to be root).

### Installing the software
    $ sudo ./install.sh

############
Installation
############

The Quick Way
===============
To install pifacecommon with minimal fuss::

    $ git clone https://github.com/piface/pifacecommon.git
    $ cd pifacecommon
    $ sudo python3 setup.py install

Then reboot.

You can also get pifacecommon from PyPi::

    $ sudo easy_install3 pifacecommon


The Slow Way
============
This is a more detailed description of the installation. You will have to reboot
after setting up SPI and GPIO permissions.

Enable the SPI module
---------------------
PiFace boards communicate with the Raspberry Pi through the SPI interface.
The SPI interface driver is included in the latest Raspbian distributions
but is not enabled by default. You can load the SPI driver manually by running::

    $ sudo modprobe spi-bcm2708

And you can permanently enable it by running this command::

    $ curl https://raw.github.com/piface/pifacecommon/master/bin/unblacklist-spi-bcm2708.sh | sudo bash

The /dev/spidev* devices should now appear but they require special privileges
for the user *pi* to access them. You can set these up by running::

    $ curl https://raw.github.com/piface/pifacecommon/master/bin/spidev-setup.sh | sudo bash

Enable GPIO access
------------------
Interrupts work by monitoring the GPIO pins. You'll need to give the user *pi*
access to these pins by running the following command::

    $ curl https://raw.github.com/piface/pifacecommon/master/bin/gpio-setup.sh | sudo bash

Building and installing
-----------------------
Download and install with::

    $ git clone https://github.com/piface/pifacecommon.git
    $ cd pifacecommon/

Edit the setup.py file so that MODULE_ONLY is True. Then run::

    $ sudo python3 setup.py install

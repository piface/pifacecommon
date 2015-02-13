############
Installation
############

Install
=======
apt-get
-------
Make sure you are using the lastest version of Raspbian::

    $ sudo apt-get update
    $ sudo apt-get upgrade

Install ``pifacecommon`` (for Python 3 and 2) with the following command::

    $ sudo apt-get install python{,3}-pifacecommon

You will also need to set up automatic loading of the SPI kernel module which
can be done with the lastest version of ``raspi-config``. Run::

    $ sudo raspi-config

Then navigate to ``Advanced Options``, ``SPI`` and select ``yes``.

You may need to reboot.


Manually
--------
This is a more detailed description of the installation. You will have
to reboot after setting up SPI and GPIO permissions.

Building and installing
^^^^^^^^^^^^^^^^^^^^^^^

Download and install with::

    $ git clone https://github.com/piface/pifacecommon.git
    $ cd pifacecommon/
    $ sudo python3 setup.py install

.. note:: Subtitute ``python3`` for ``python`` if you want to install for
   Python 2.


Enable the SPI module
^^^^^^^^^^^^^^^^^^^^^
PiFace boards communicate with the Raspberry Pi through the SPI interface.
The SPI interface driver is included in the latest Raspbian distributions
but is not enabled by default. You can load the SPI driver manually by running::

    $ sudo modprobe spi-bcm2708

You can permanently enable it one of two ways, depending on which kernel
version you're on.

- Kernel Version < 3.18 (The old way): Comment out ``blacklist spi-bcm2708`` line in ``/etc/modprobe.d/raspi-blacklist.conf``.

- Kernel Version >= 3.18 (Device Tree): add ``dtparam=spi=on`` to ``/boot/config/txt``

The /dev/spidev* devices should now appear but they require special privileges
for the user *pi* to access them. You can set these up by adding the following
`udev rule <https://wiki.debian.org/udev>`_ to
``/etc/udev/rules.d/50-spi.rules``::

    KERNEL=="spidev*", GROUP="spi", MODE="0660"

Then create the spi group and add the user pi::

    $ groupadd spi
    $ gpasswd -a pi spi

.. note:: To enable other users to access SPI devices (PiFace, for example)
   you can add them to the ``spi`` group with ``gpasswd -a otheruser spi``.


Enable GPIO access
^^^^^^^^^^^^^^^^^^
Interrupts work by monitoring the GPIO pins. You'll need to give the user *pi*
access to these by adding the following udev rule (all on one line) to
``/etc/udev/rules.d/51-gpio.rules``::

    SUBSYSTEM=="gpio*", PROGRAM="/bin/sh -c 'chown -R root:gpio /sys/class/gpio && chmod -R 770 /sys/class/gpio'"

Then create the gpio group and add the user pi::

    $ groupadd gpio
    $ gpasswd -a pi gpio

Uninstall
=========

::

    $ sudo apt-get remove python{,3}-pifacecommon

############
Installation
############

Install
=======

.. note:: Subtitute ``python3`` for ``python`` and
   ``easy_install3`` for ``easy_install`` if you want to install for
   Python 2.

Automatically
-------------

Download the latest release from
`here <https://github.com/piface/pifacecommon/releases>`_. Then install with::

    $ dpkg -i python3-pifacecommon_2.0.3-1_all.deb

Or you can install without using your package manager::

    $ git clone https://github.com/piface/pifacecommon.git
    $ cd pifacecommon/
    $ sudo python3 setup.py install
    $ sudo bin/post-installation.sh


Manually
--------
This is a more detailed description of the installation. You will have to reboot
after setting up SPI and GPIO permissions.

Building and installing
^^^^^^^^^^^^^^^^^^^^^^^

Download and install with::

    $ git clone https://github.com/piface/pifacecommon.git
    $ cd pifacecommon/
    $ sudo python3 setup.py install


Enable the SPI module
^^^^^^^^^^^^^^^^^^^^^
PiFace boards communicate with the Raspberry Pi through the SPI interface.
The SPI interface driver is included in the latest Raspbian distributions
but is not enabled by default. You can load the SPI driver manually by running::

    $ sudo modprobe spi-bcm2708

And you can permanently enable it by commenting out the
``blacklist spi-bcm2708`` line in ``/etc/modprobe.d/raspi-blacklist.conf``.

The /dev/spidev* devices should now appear but they require special privileges
for the user *pi* to access them. You can set these up by adding the following
rule to ``/etc/udev/rules.d/50-spi.rules``::

    KERNEL=="spidev*", GROUP="spi", MODE="0660"

Then create the spi group and add the user pi::

    $ groupadd spi
    $ gpasswd -a pi spi


Enable GPIO access
^^^^^^^^^^^^^^^^^^
Interrupts work by monitoring the GPIO pins. You'll need to give the user *pi*
access to these by adding the following udev rule to
``/etc/udev/rules.d/51-gpio.rules``::

    SUBSYSTEM=="gpio*", PROGRAM="
    /bin/sh -c 'chown -R root:gpio /sys/class/gpio &&
    chmod -R 770 /sys/class/gpio;
    chown -R root:gpio /sys/devices/virtual/gpio &&
    chmod -R 770 /sys/devices/virtual/gpio'"

Then create the gpio group and add the user pi::

    $ groupadd gpio
    $ gpasswd -a pi gpio

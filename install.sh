#!/bin/bash
#: Description: Installs pifacecommon and its dependecies

# check if the script is being run as root
if [[ $EUID -ne 0 ]]
then
	printf 'This script must be run as root.\nExiting..\n'
	exit 1
fi

# unblacklist spi
./unblacklist-spi-bcm2708.sh
if [ $? -ne 0 ]
then
    printf "Failed to unblacklist spi-bcm2708.\nExiting...\n"
    exit 1
fi

# set up spidev permissions
./spidev-setup.sh
if [ $? -ne 0 ]
then
    printf "Failed to setup spidev.\nExiting...\n"
    exit 1
fi

# install python library
printf "Installing pifacecommon...\n"
python3 setup.py install
printf "Done!\n"

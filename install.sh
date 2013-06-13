#!/bin/bash
#: Description: Installs pifacecommon and its dependecies

# check if the script is being run as root
if [[ $EUID -ne 0 ]]
then
	printf 'This script must be run as root.\nExiting..\n'
	exit 1
fi

# unblacklist spi
./scripts/unblacklist-spi-bcm2708.sh
if [ $? -ne 0 ]
then
    printf "Failed to unblacklist spi-bcm2708.\nExiting...\n"
    exit 1
fi

# set up spidev permissions
./scripts/spidev-setup.sh
if [ $? -ne 0 ]
then
    printf "Failed to setup spidev.\nExiting...\n"
    exit 1
fi

# install python library

# install python3 setup tools
#aptitude install python3-setuptools
apt-get install -y python3-setuptools # apt-get is slightly faster

printf "Building egg...\n"
python3 setup.py bdist_egg

# tp - ultimately I want to just distribute the egg
printf "Installing pifacecommon...\n"
easy_install3 dist/pifacecommon-1.0-py3.2.egg
printf "Done!\n"

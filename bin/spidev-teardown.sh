#!/bin/bash
#: Description: Removes permissions for the spi devices
#:      Author: Thomas Preston

udev_rules_file='/etc/udev/rules.d/50-spi.rules'
spi_group_name='spiuser'

# check if the script is being run as root
if [[ $EUID -ne 0 ]]
then
    printf 'This script must be run as root.\nExiting..\n'
    exit 1
fi

# check that the rules file exists
if [ -f $udev_rules_file ]
then
    printf 'Removing udev rule.\n'
    rm $udev_rules_file
else
    printf 'The spi rules file does not exist.\nExiting...\n'
    exit 0
fi

printf "Removing group $spi_group_name.\n"
groupdel $spi_group_name

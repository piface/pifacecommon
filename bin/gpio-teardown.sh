#!/bin/bash
#: Description: Removes permissions for the gpio devices
#:      Author: Thomas Preston

udev_rules_file='/etc/udev/rules.d/51-gpio.rules'
gpio_group_name='gpio'

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
    printf 'The gpio rules file does not exist.\nExiting...\n'
    exit 0
fi

printf "Removing group $gpio_group_name.\n"
groupdel $gpio_group_name

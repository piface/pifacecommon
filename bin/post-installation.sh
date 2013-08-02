#!/bin/bash
#: Description: Post installation script for pifacecommon.

create_group() {
    printf "Creating group '%s'\n" $1
    groupadd $1
}

add_user_to_group() {
    gpasswd -a $1 $2
}

#=======================================================================
# NAME: unbacklist_spi
# DESCRIPTION: Unblacklist spi-bcm2708 in the raspi-blacklist.conf file.
#=======================================================================
unbacklist_spi() {
    blacklist_file="/etc/modprobe.d/raspi-blacklist.conf"
    blacklist_string="blacklist spi-bcm2708"
    unblacklist_string="#$blacklist_string # unblacklist for PiFace"
    tmp_blacklist_file="/tmp/new_backlist_file$(date +%Y%m%d%H%M)"

    # if the file exists, unblacklist, backup, overwrite
    printf 'Unblacklisting spi-bcm2708.\n'
    if [[ -a $blacklist_file ]]; then
        sed "s/^$blacklist_string$/$unblacklist_string/" \
            $blacklist_file >> $tmp_blacklist_file
        cp $blacklist_file $blacklist_file.old
        mv $tmp_blacklist_file $blacklist_file
    fi
}

#=======================================================================
# NAME: setup_spi
# DESCRIPTION: Sets up permissions for the spi devices
#=======================================================================
setup_spi() {
    udev_rules_file='/etc/udev/rules.d/50-spi.rules'
    spi_group_name='spi'
    rule="KERNEL==\"spidev*\", GROUP=\"${spi_group_name}\", MODE=\"0660\""

    printf 'Creating spi udev rule.\n'
    if [ -f $udev_rules_file ]; then
        printf 'The spi rules file already exists.\n'
    else
        echo $rule > $udev_rules_file # create the rules file
    fi

    create_group $spi_group_name
    add_user_to_group pi $spi_group_name

    printf 'User "pi" can now access the /dev/spidev* devices.\n'
}

#=======================================================================
# NAME: setup_gpio
# DESCRIPTION: Sets up permissions for the gpio devices
#=======================================================================
setup_gpio() {
    udev_rules_file='/etc/udev/rules.d/51-gpio.rules'
    gpio_group_name='gpio'
    rule="SUBSYSTEM==\"gpio*\", PROGRAM=\"/bin/sh -c 'chown -R root:${gpio_group_name} /sys/class/gpio && chmod -R 770 /sys/class/gpio; chown -R root:${gpio_group_name} /sys/devices/virtual/gpio && chmod -R 770 /sys/devices/virtual/gpio'\""

    printf 'Creating gpio udev rule\n'
    if [ -f $udev_rules_file ]; then
        printf 'The gpio rules file already exists.\n'
    else
        echo  $rule > $udev_rules_file # create the rules file
    fi

    create_group $gpio_group_name
    add_user_to_group pi $gpio_group_name

    printf 'User "pi" can now access the virtual gpio devices.\n'
}

#=======================================================================
# MAIN
#=======================================================================
# check if the script is being run as root
if [[ $EUID -ne 0 ]]
then
    printf 'This script must be run as root.\nExiting..\n'
    exit 1
fi
unbacklist_spi
setup_spi
setup_gpio
printf 'Please *reboot* before using your PiFace product.\n'

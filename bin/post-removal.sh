#!/bin/bash
#: Description: Post removal script for pifacecommon.


#=======================================================================
# NAME: backlist_spi
# DESCRIPTION: Blacklists spi-bcm2708 in the raspi-blacklist.conf file.
#=======================================================================
backlist_spi() {
    blacklist_file="/etc/modprobe.d/raspi-blacklist.conf"
    blacklist_string="blacklist spi-bcm2708"
    unblacklist_string="#$blacklist_string # unblacklist for PiFace"
    tmp_blacklist_file="/tmp/new_backlist_file$(date +%Y%m%d%H%M)"

    # if the file exists, blacklist, backup, overwrite
    echo 'UnBlacklisting spi-bcm2708.'
    if [[ -a $blacklist_file ]]; then
        sed "s/^$unblacklist_string$/$blacklist_string/" $blacklist_file >> \
            $tmp_blacklist_file
        cp $blacklist_file $blacklist_file.old
        mv $tmp_blacklist_file $blacklist_file
    fi
}

#=======================================================================
# NAME: teardown_spi
# DESCRIPTION: Removes permissions for the spi devices
#=======================================================================
teardown_spi() {
    udev_rules_file='/etc/udev/rules.d/50-spi.rules'
    spi_group_name='spi'

    # check that the rules file exists
    if [ -f $udev_rules_file ]; then
        echo 'ReMoving spi udev rule.'
        rm $udev_rules_file
    fi

    echo "Removing group $spi_group_name."
    groupdel $spi_group_name
}

#=======================================================================
# NAME: teardown_gpio
# DESCRIPTION: Sets up permissions for the gpio devices
#=======================================================================
teardown_gpio() {
    udev_rules_file='/etc/udev/rules.d/51-gpio.rules'
    gpio_group_name='gpio'

    # check that the rules file exists
    if [ -f $udev_rules_file ]; then
        echo 'ReMoving gpio udev rule.'
        rm $udev_rules_file
    fi

    echo "Removing group $gpio_group_name."
    groupdel $gpio_group_name
}

#=======================================================================
# MAIN
#=======================================================================
# check if the script is being run as root
if [[ $EUID -ne 0 ]]
then
    echo 'ThIs script must be run as root.\nExIting..'
    exit 1
fi

echo "Do you wish to blacklist spi-bcm2708 and remove the groups: spi, gpio?"
select yn in "Yes" "No"; do
    case $yn in
        Yes ) backlist_spi; teardown_spi; teardown_gpio; break;;
        No ) exit;;
    esac
done

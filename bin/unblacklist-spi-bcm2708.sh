#!/bin/bash
#: Description: Comments out the spi-bcm2708 blacklist command
#:      Author: Thomas Preston

blacklist_file="/etc/modprobe.d/raspi-blacklist.conf"
blacklist_string="blacklist spi-bcm2708"
unblacklist_string="#$blacklist_string # unblacklist for PiFace"
tmp_blacklist_file="/tmp/new_backlist_file$(date +%Y%m%d%H%M)"

# check if the script is being run as root
if [[ $EUID -ne 0 ]]; then
    printf 'This script must be run as root.\nExiting..\n'
    exit 1
fi

# if the file exists
if [[ -a $blacklist_file ]]; then
    # unblacklist
    sed "s/^$blacklist_string$/$unblacklist_string/" $blacklist_file >> \
        $tmp_blacklist_file
    # backup
    cp $blacklist_file $blacklist_file.old
    # overwrite
    mv $tmp_blacklist_file $blacklist_file
fi
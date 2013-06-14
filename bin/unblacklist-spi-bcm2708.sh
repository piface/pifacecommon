#!/bin/bash
#: Description: Comments out the spi-bcm2708 blacklist command
#:      Author: Thomas Preston

blacklist_file="/etc/modprobe.d/raspi-blacklist.conf"
blacklist_string="blacklist spi-bcm2708"
tmp_blacklist_file="/tmp/new_backlist_file$(date +%Y%m%d%H%M)"

# check if the script is being run as root
if [[ $EUID -ne 0 ]]; then
    printf 'This script must be run as root.\nExiting..\n'
    exit 1
fi

# if the file exists
if [[ -a $blacklist_file ]]; then
    blacklist_count=$(grep -c "^$blacklist_string" $blacklist_file)
    
    if [[ $blacklist_count -gt 0 ]]; then
        # remove all mentions of spi module
        grep -v "$blacklist_string" $blacklist_file > $tmp_blacklist_file
        
        # unblacklist
        echo "#$blacklist_string # unblacklist for PiFace" >> $tmp_blacklist_file
        
        # overwrite
        cp $blacklist_file $blacklist_file.old
        mv $tmp_blacklist_file $blacklist_file
    fi
fi
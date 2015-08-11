#! /bin/sh
hostid=$1
subip=$2
vlanid=$3
intf=$(eval 'ifconfig | grep -o "\<h[0-9]\+-eth[0-9]\+\.$vlanid\>"')
ping -I $intf 192.168.${subip}.${hostid}

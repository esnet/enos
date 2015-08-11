#! /bin/sh
hostid=$1

ifid=eth1
subip=$2
vlanid=$3

vconfig add h${hostid}-${ifid} ${vlanid}
ifconfig h${hostid}-${ifid}.${vlanid} up
ifconfig h${hostid}-${ifid}.${vlanid} 192.168.${subip}.${hostid}/24


#! /bin/sh
hostid=$1

ifid=eth1
vlanid=$2

vconfig add h${hostid}-${ifid} ${vlanid}
ifconfig h${hostid}-${ifid}.${vlanid} up
ifconfig h${hostid}-${ifid}.${vlanid} 192.168.${vlanid}.${hostid}/24


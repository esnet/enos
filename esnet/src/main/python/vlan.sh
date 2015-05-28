#! /bin/sh
hostid=$1

ifid=eth1
vlanid=10

vconfig add h${hostid}-${ifid} ${vlanid}
ifconfig h${hostid}-${ifid}.${vlanid} up
ifconfig h${hostid}-${ifid}.${vlanid} 192.168.1.${hostid}/24


#! /bin/sh

# syntax vlan.sh <interface>  <ip> <vlan>. i.e. vlan.sh h4-eth1 192.168.1.4 10

ifid=$1

ip=$2

vlanid=$3



vconfig add ${ifid} ${vlanid}

ifconfig ${ifid}.${vlanid} ${ip} up
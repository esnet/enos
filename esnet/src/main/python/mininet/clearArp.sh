#! /bin/sh
ips=$(eval 'arp | grep -o "\<192\.168\.[0-9]\+\.[0-9]\+\>"')
for ip in ${ips}
do
	arp -d ${ip}
done

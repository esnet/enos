#! /bin/sh
i=1
while [ $i -le $1 ]; do
	sudo ovs-ofctl del-flows s$i
	i=$(( i + 1 ))
done

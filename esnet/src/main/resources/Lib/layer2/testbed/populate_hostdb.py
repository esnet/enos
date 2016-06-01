#/usr/bin/python
#
# ESnet Network Operating System (ENos) Copyright (c) 2015, The Regents
# of the University of California, through Lawrence Berkeley National
# Laboratory (subject to receipt of any required approvals from the
# U.S. Dept. of Energy).  All rights reserved.
#
# If you have questions about your rights to use or distribute this
# software, please contact Berkeley Lab's Innovation & Partnerships
# Office at IPO@lbl.gov.
#
# NOTICE.  This Software was developed under funding from the
# U.S. Department of Energy and the U.S. Government consequently retains
# certain rights. As such, the U.S. Government has been granted for
# itself and others acting on its behalf a paid-up, nonexclusive,
# irrevocable, worldwide license in the Software to reproduce,
# distribute copies to the public, prepare derivative works, and perform
# publicly and display publicly, and to permit other to do so.
#

from layer2.testbed import idmanager, tbip, tbhost

def print_help():
    "Help message for id management utility"
    print "ESnet Testbed id management utility"
    print "populate_hostdb <file>"
    print " Commands are:"
    print "\thelp"
    print "\t\tPrints this help."
    print "\tcp <file>"
    print "\t\tCSV file location. parses control plane ip file, creates host resources and populates db"
    print "\tdp <file>"
    print "\t\tCSV file location. parses data plane ip file, creates host resources and populates db"

HOST_IP = "ipaddress"
HOST_NETMASK = 24
HOST_OS="unknown"
HOST_HYPERVISOR= "Unknown"
HOST_PROJECT=0
HOST_DESCRIPTION=""

HOST_CP_INTERFACE = "eth0"

if __name__ == '__main__':
    argv = sys.argv

    if len(argv) == 1:
        print_help()
        sys.exit()
    cmd = argv[1]
    if cmd == "help":
        print_help()
    elif cmd == 'cp':
    	filelocation = argv[2]

    	f = open(filelocation,"r")
    	
    	for line in f:
    		line.strip()
    		fields = line.split(",")

    		hostname = fields[0].strip()
    		ipaddress = fields[1].strip()
    		hosttype = fields[2].strip()
    		owner = fields[3].strip()
    		description = fields[4].strip()
    		if(hostname == 'Host'):
    			continue

    		hostid = ipaddress.split(".")[3]
    		print hostid
    		#register id
    		idmanager.register(hostid,hostname,owner,0)

    		#register control plane ip
    		tbip.register_ip(hostname, owner, HOST_PROJECT, hosttype, HOST_OS, description, ipaddress, HOST_NETMASK)

    		tbhost.createHostTemplateWithId(hostname, HOST_HYPERVISOR, owner, HOST_PROJECT, hostid, HOST_OS)

    		tbhost.addIP(hostname, HOST_CP_INTERFACE, ipaddress)

    elif cmd == 'dp':
    	filelocation = argv[2]

    	f = open(filelocation,"r")

    	for line in f:
    		line.strip()
    		fields = line.split(",")
    		hostname = fields[0].strip()

    		interface = fields[2].strip()
    		ipaddress = fields[3].strip()
    		hosttype="Container"
    		project = fields[5].strip()
    		owner = fields[6].strip()
    		if(hostname == 'Host'):
    			continue
    		print hostname
    		print interface
    		print ipaddress
    		print hosttype
    		print project
    		tbip.register_ip(hostname, owner, HOST_PROJECT, hosttype, HOST_OS, description, ipaddress, HOST_NETMASK)
    		tbhost.addIP(hostname, interface, ipaddress)













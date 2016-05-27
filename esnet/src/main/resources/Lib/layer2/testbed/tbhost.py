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

""" This module manages testbed hosts - creation, deletion, starting, stopping"""

from net.es.netshell.api import Resource, Container
from layer2.testbed import idmanager

HOST_CONTAINER = 'host'

HOSTNAME = 'host'
HOSTID = 'id'
HYPERVISOR = 'hypervisor'
OWNER = 'owner'
PROJECT = 'project'
PROPERTIES = 'properties'

def exists(hostname):
	container = Container.getContainer(HOST_CONTAINER)
	if container.loadResource(hostname):
		return True
	else:
		return False

def createHostTemplateWithId(host, hypervisor, owner, project, hostid):
	container = Container.getContainer(HOST_CONTAINER)

	if not exists(host):

		#Create host resource and save
		hostresource = Resource(host)
		hostresource.properties[HOSTNAME] = host
		hostresource.properties[HOSTID] = hostid
		hostresource.properties[HYPERVISOR] = hypervisor
		hostresource.properties[OWNER] = owner
		hostresource.properties[PROJECT] = project

		container.saveResource(hostresource)
	else:
		raise ValueError("Attempting to create duplicate host")


def createHostTemplate(host, hypervisor, owner, project):
	if not exists(host):
		#get next available id for host
		try:
			hostid = idmanager.allocate(host,owner,project)
			createHostTemplateWithId(host, hypervisor, owner, project, hostid)
		except ValueError as e:
			print "Error allocating unique id. Please register an id manually"
	else:
		raise ValueError("ERROR: Host template exists.")


def print_help():
    "Help message for tbhost utility"
    print "ESnet Testbed Host Utility"
    print "tbip <cmd> <cmds options>"
    print " Commands are:"
    print "\thelp"
    print "\t\tPrints this help."
    print "\tcreate <hostname> hypervisor <hypervisor> owner <owner> project <project> [id <id>]"
    print "\t\tCreates container template and gets an id for the container"

if __name__ == '__main__':
    argv = sys.argv

    if len(argv) == 1:
        print_help()
        sys.exit()
    cmd = argv[1]
    if cmd == "help":
        print_help()
    elif cmd == 'create':
        if (len(argv)) < 9:
            print "ERROR: Argument mismatch"
            print_help()
        else:
            host = argv[2]

            if argv[3] == 'hypervisor':
                hypervisor = argv[4]
            else:

                print "ERROR: Argument mismatch"
                print_help()
                sys.exit()

            if argv[5] == 'owner':
                owner = argv[6]
            else:

                print "ERROR: Argument mismatch"
                print_help()
                sys.exit()

            if argv[7] == 'project':
                pid = argv[8]
            else:
                print "ERROR: Argument mismatch"
                print_help()
                sys.exit()

            if len(argv)>9 and argv[9] == 'id':
                hostid = argv[10]

            try:
            	if(len(argv)>9):
            		createHostTemplateWithId(host,hypervisor,owner,pid, hostid)
                	print "Host template created"
                else:
                	createHostTemplate(host,hypervisor,owner,pid)
                	print "Host template created"
            except ValueError as e:
                print e
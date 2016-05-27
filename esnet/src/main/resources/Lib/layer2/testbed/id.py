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

""" This module manages ID allocation/deallocation."""

from net.es.netshell.api import Resource, Container

ID_MAX = 255
ID_MIN = 0

ID_CONTAINER='id'
RESOURCEID = 'id'
HOST = 'host'
OWNER = 'owner'
PROJECT = 'project'

def register(hostid, host, owner, pid):
	""" This method creates the ID resource from the given arguments and registers it in persistent storage """
	
	hid = int(hostid)
	if (hid<ID_MIN or hid>ID_MAX):
		raise ValueError('ID out of range')

	idresource = Resource(hostid)
	idresource.properties[HOST] = host
	idresource.properties[PROJECT] = pid
	idresource.properties[OWNER] = owner
	idresource.properties[RESOURCEID] = hid

	container = Container.getContainer(ID_CONTAINER)
	idexists = container.loadResource(hostid)
	if idexists == None:
		container.saveResource(idresource)
	else:
		raise ValueError('ID exists. Attempting duplicate registration')

def print_help():
    "Help message for id management utility"
    print "ESnet Testbed id management utility"
    print "id <cmd> <cmds options>"
    print " Commands are:"
    print "\thelp"
    print "\t\tPrints this help."
    print "\tregister"
    print "\t\tregister id <id> host <hostname> owner <owner> project <pid>"
    print "\t\tRegisters id in database"


if __name__ == '__main__':
    argv = sys.argv

    if len(argv) == 1:
        print_help()
        sys.exit()
    cmd = argv[1]
    if cmd == "help":
        print_help()
    elif cmd == 'register':
        if (len(argv)) != 10:
            print "ERROR: Argument mismatch"
            print_help()
        else:
			if argv[2] == 'id':
				try:
					int(argv[3])
				except:
					print "ERROR: ID must be integer"
				hostid = argv[3]
			else:
				print "ERROR: Argument mismatch"
				print_help()
				sys.exit()

			if argv[4] == 'host':
				host = argv[5]
			else:
				print "ERROR: Argument mismatch"
				print_help()
				sys.exit()

			if argv[6] == 'owner':
				owner = argv[7]
			else:
				print "ERROR: Argument mismatch"
				print_help()
				sys.exit()

			if argv[8] == 'project':
				pid = argv[9]
			else:
				print "ERROR: Argument mismatch"
				print_help()
				sys.exit()

			try:
				register(hostid,host,owner,pid)
				print "ID:"+hostid+" registered"
			except ValueError as e:
				print e


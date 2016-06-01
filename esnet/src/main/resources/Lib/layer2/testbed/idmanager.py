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
IDRESOURCE_RESOURCEID = 'id'
IDRESOURCE_HOST = 'host'
IDRESOURCE_OWNER = 'owner'
IDRESOURCE_PROJECT = 'project'

DBQ_LESSER = '$lt'
DBQ_GREATER = '$gte'
PROPERTIES = 'properties'

def getid():
    """ Returns the next available id """
    rangequery = {}
    rangequery[DBQ_LESSER] = ID_MAX
    rangequery[DBQ_GREATER] = ID_MIN

    query = {}
    key = PROPERTIES+"."+IDRESOURCE_RESOURCEID

    query[key] = rangequery
    container = Container.getContainer(ID_CONTAINER)
    idresources = container.loadResources(query)

    ##0, 1 and 2 are reserved ids;
    idbitmap = [0 for i in range(ID_MAX+1)]
    if (len(idbitmap)>0):
        idbitmap[0]=1
    if (len(idbitmap)>1):
        idbitmap[1]=1
    if (len(idbitmap)>2):
        idbitmap[2]=1

    for idresource in idresources:
        idbitmap[idresource.properties[IDRESOURCE_RESOURCEID]] = 1

    for i in range(ID_MAX+1):
        if idbitmap[i] == 0:
            return i

    raise ValueError('All ids have been allocated')

def register(hostid, host, owner, pid):
    """ This method creates the ID resource from the given arguments and registers it in persistent storage """
    
    hid = int(hostid)
    if (hid<ID_MIN or hid>ID_MAX):
        raise ValueError('ID out of range')

    idresource = Resource(hostid)
    idresource.properties[IDRESOURCE_HOST] = host
    idresource.properties[IDRESOURCE_PROJECT] = pid
    idresource.properties[IDRESOURCE_OWNER] = owner
    idresource.properties[IDRESOURCE_RESOURCEID] = hid
    container = Container.getContainer(ID_CONTAINER)
    idexists = container.loadResource(hostid)
    if idexists == None:
        container.saveResource(idresource)
    else:
        raise ValueError('ID exists. Attempting duplicate registration')

def allocate(host, owner, pid):
    """ This method creates the ID resource from the given arguments and registers it in persistent storage """
    
    hid = getid()
    if (hid<ID_MIN or hid>ID_MAX):
        raise ValueError('Error allocating ID')

    register(str(hid), host, owner, pid)
    return hid

def remove(hostid):
    """ This method removes the ID resource from persistent storage"""
    
    hid = int(hostid)
    if (hid<ID_MIN or hid>ID_MAX):
        raise ValueError('ID out of range')

    if exists(hostid):
        container = Container.getContainer(ID_CONTAINER)
        container.deleteResource(hostid)
        if exists(hostid):
            raise ValueError("Error deleting resource")
    else:
        raise ValueError("Id resource does not exist")


def exists(hostid):
    """ This method checks if the ID resource exists in persistent storage"""
    
    hid = int(hostid)
    if (hid<ID_MIN or hid>ID_MAX):
        raise ValueError('ID out of range')

    container = Container.getContainer(ID_CONTAINER)
    idexists = container.loadResource(hostid)

    if idexists != None:
        return True
    else:
        return False


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
    print "\tnext"
    print "\t\tDisplays the next available id"
    print "\tremove"
    print "\t\tremove <id>"
    print "\t\tRemoves the id" 


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
    elif cmd == 'next':
        try:
            idresource = getid()
            print idresource
        except ValueError:
            print "ERROR: All values have been allocated"
    elif cmd == 'remove':
        if (len(argv)) != 3:
            print "ERROR: Argument mismatch"
            print_help()
        else:
            hostid = argv[2]
            try:
                remove(hostid)
                print "ID: "+hostid+" Deleted"
            except ValueError as e:
                print "Error deleting id resource"
    elif cmd == 'allocate':
        if (len(argv)) != 8:
            print "ERROR: Argument mismatch"
            print_help()
        else:
            if argv[2] == 'host':
                host = argv[3]
            else:
                print "ERROR: Argument mismatch"
                print_help()
                sys.exit()

            if argv[4] == 'owner':
                owner = argv[5]
            else:
                print "ERROR: Argument mismatch"
                print_help()
                sys.exit()

            if argv[6] == 'project':
                pid = argv[7]
            else:
                print "ERROR: Argument mismatch"
                print_help()
                sys.exit()
            try:
                hostid = allocate(host,owner,pid)
                print "Allocated ID:"+str(hostid)+" registered"
            except ValueError as e:
                print e

    else:
        print_help()
        sys.exit()


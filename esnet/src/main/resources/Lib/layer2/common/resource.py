#!/usr/bin/python
#
# ESnet Network Operating System (ENOS) Copyright (c) 2015, The Regents
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

from net.es.netshell.api import Container

def getResource(containerName,resourceName,owner=None):
    container = None
    if owner != None:
        container = Container.getContainer(owner,containerName)
    else:
        container = Container.getContainer(containerName)
    resource = container.loadResource(resourceName)
    return resource

def showResource(containerName,resourceName,owner=None):
    resource = getResource(containerName,resourceName,owner)
    if resource == None:
        print "resource does not exist"
        return
    print resource.toPrettyString()

def print_syntax():
    print "Resource Utility"
    print "resource <cmd> <cmds options>"
    print " Commands are:"
    print "\thelp"
    print "\t\tPrints this help."
    print "\tresource show <resource name> <container name> owner <user name>"
    print "\t\tDisplays a resource in a container. Current user is assumed if optional owner is not provided."

def processCLI(argv):
    if len(argv) == 1:
        print_syntax()
        return
    cmd = argv[1]
    if cmd == "help":
        print_syntax()
        return


    if cmd == "show":
        resourceName = argv[2]
        containerName = argv[3]
        owner = None
        if len(argv) > 4:
            owner = argv[5]
        showResource(resourceName = resourceName,containerName=containerName,owner=owner)
        return
    else:
        print "unknown command"
        print_syntax()

if __name__ == '__main__':
    processCLI(sys.argv)
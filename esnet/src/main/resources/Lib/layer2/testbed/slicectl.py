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

import threading

from net.es.netshell.api import Container,Resource, ResourceTypes

Inventory = "inventory"
AllocatedResources ="allocatedUseResources"
Slices = "slices"
SliceOwner = "sliceOwner"
SliceId = "sliceId"

if not 'multiplexerSlices' in globals():
    globals()['multiplexerSlices'] = {}

if not 'slicerLock' in globals():
    globals()['slicerLock'] = threading.Lock()


def loadSlices():
    multiplexerSlices = globals()['multiplexerSlices']
    slices = Container.getContainer(Slices)
    allocatedSlices = slices.loadResources({"resourceType":ResourceTypes.SLICE})
    for slice in allocatedSlices:
        multiplexerSlices[slice.getResourceName] = slice


"""
The MP-VPN Multiplexer uses an inventory container in order to store the switches and routers it
owns.
"""
def checkSlicerEnvironment():
    slices = Container.getContainer(Slices)
    if not "initialized" in slices.properties:
        # First time the MP-VPN Multiplexer is used. Need to intialize inventory
        print "First time running this command."
        print "creating MP-VPN Multiplexer environment. May takes a few seconds."
        from layer2.testbed.tbctl import createinv
        createinv(toponame=Inventory)
        slices.properties["initialized"] = True
        slices.save()
        print slices
        print "done"
    else:
        loadSlices()

def allocateNewID():
    # this code allocates a new ID. ID are 8 bits.
    # TBD needs to be a critical section.
    multiplexerSlices = globals()['multiplexerSlices']
    slicerLock = globals()['slicerLock']
    with slicerLock:
        for id in range(1,255):
            if id in multiplexerSlices:
                continue
            return id
        return 0

def createSlice(name,owner,id=None):
    multiplexerSlices = globals()['multiplexerSlices']
    if id in multiplexerSlices:
        print "id ",id," exists already."
    else:
        id = allocateNewID()
    slice = Resource(str(id))
    slice.setDescription(name)
    slice.properties[SliceOwner] = owner
    slices = Container.getContainer(Slices)
    slices.save(slice)
    multiplexerSlices[id] = slice
    return 0

def deleteSlice(id):
    multiplexerSlices = globals()['multiplexerSlices']
    if id in multiplexerSlices:
        slices = Container.getContainer(Slices)
        slices.deleteResource(id)
    else:
        print "slice ",id," does not exist"


def print_syntax():
    print "MP-VPN Multiplex Utility"
    print "slicectl <cmd> <cmds options>"
    print " Commands are:"
    print "\thelp"
    print "\t\tPrints this help."
    print "\tslicectl create-slice <slice name> owner <user name> [id <id>]"
    print "\tslicectl delete-slice <id>"
    print "\tslicectl list-slices [grep <pattern>"
    print "\tslicectl add-port <slice id> switch <switch name> port <port name> [vlan <VLAN>]"
    print "\tslicectl del-port <slice id> switch <switch name> port <port name> [vlan <VLAN>"
    print "\tslicectl list-ports <slice id> [switch <switch name>]"



def processCLI(argv):
    if len(argv) == 1:
        print_syntax()
        return
    cmd = argv[1]
    if cmd == "help":
        print_syntax()
        return

    checkSlicerEnvironment()

    if cmd == "create-slice":
        sliceName = argv[2]
        owner = argv[4]
        id = None
        if len(argv) > 4:
            id = argv[6]
        rid = createSlice(name = sliceName,owner=owner,id=id)
        if (id < 0):
            print "failed to create slice"
            return
        print "slice created id= ", rid
    else:
        print "unknown command"
        print_syntax()

if __name__ == '__main__':
    processCLI(sys.argv)
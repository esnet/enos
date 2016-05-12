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
        multiplexerSlices[slice.getResourceName()] = slice


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
            id = str(id)
            if id in multiplexerSlices:
                continue
            return id
        return None

def createSlice(name,owner,id=None):
    multiplexerSlices = globals()['multiplexerSlices']
    id = str(id)
    if id in multiplexerSlices:
        print "id ",id," exists already."
    else:
        id = allocateNewID()
        if id == None:
            print("cannot allocate new slice id")
            return None
    slice = Resource(id)
    slice.setDescription(name)
    slice.properties[SliceOwner] = owner
    slice.setResourceType(ResourceTypes.SLICE)
    slices = Container.getContainer(Slices)
    slices.saveResource(slice)
    multiplexerSlices[id] = slice
    return id

def deleteSlice(id):
    id = str(id)
    multiplexerSlices = globals()['multiplexerSlices']
    slicerLock = globals()['slicerLock']
    with slicerLock:
        if id in multiplexerSlices:
            slices = Container.getContainer(Slices)
            slices.deleteResource(id)
            del multiplexerSlices[id]
        else:
            print "slice ",id," does not exist"

def displaySlices(owner=None):
    multiplexerSlices = globals()['multiplexerSlices']
    print "ID\tOwner\tDescription"
    for (sliceId,slice) in multiplexerSlices.items():
        if owner != None and slice[SliceOwner] != owner:
            continue
        print sliceId,"\t",slice.properties[SliceOwner],"\t",slice.getDescription()

def showSlice(id):
    id = str(id)
    multiplexerSlices = globals()['multiplexerSlices']
    if not id in multiplexerSlices:
        print "slice id ",id," does not exists"
        return
    slice = multiplexerSlices[id]
    print slice.toPrettyString()

def getSlices():
    return globals()['multiplexerSlices']

def print_syntax():
    print "MP-VPN Multiplex Utility"
    print "slicectl <cmd> <cmds options>"
    print " Commands are:"
    print "\thelp"
    print "\t\tPrints this help."
    print "\tslicectl create-slice <slice name> owner <user name> [id <slice id>]"
    print "\tslicectl delete-slice < slice id>"
    print "\tslicectl list-slices [owner <usr name>]"
    print "\tslicectl show-slice <slice id>"
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
        if len(argv) > 5:
            id = argv[6]
        rid = createSlice(name = sliceName,owner=owner,id=id)
        if (rid == None):
            print "failed to create slice"
            return
        print "slice created id= ", rid
        return
    elif cmd == "delete-slice":
        id = argv[2]
        deleteSlice(id)
        return
    elif cmd == "list-slices":
        owner = None
        if len(argv) > 2:
            owner = argv[3]
        displaySlices(owner=owner)
        return
    elif cmd == "show-slice":
        id = argv[2]
        showSlice(id)
        return
    else:
        print "unknown command"
        print_syntax()

if __name__ == '__main__':
    processCLI(sys.argv)
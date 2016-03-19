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

from layer2.testbed.topoctl import createtopo,addnode,addlink,getnode,Links,Nodes,Ports,Host,Hosts
from layer2.testbed.topology import TestbedTopology
from layer2.testbed.builder import tbns,poptopology,getPopRouter,testbedPops

from net.es.netshell.api import Container,Link,Resource

Role="Role"
HwSwitch = "HwSwitch"
SwSwitch = "SwSwitch"
CoreRouter = "CoreRouter"
Pops="Pops"

def createinv(toponame):
    newtopo = createtopo(toponame)
    newtopo.properties[Nodes] = {}
    newtopo.properties[Links] = {}
    topo = TestbedTopology()
    # Adds nodes
    nodes = topo.getNodes()
    for nodename in nodes:
        toponode = nodes.get(nodename)
        # Add this node to the topology
        node = addnode(toponame,nodename)
        node.getProperties().putAll(toponode.getProperties())
        newtopo.saveResource(node)
        newtopo.properties[Nodes][nodename] = newtopo.getResourceAnchor(node)

    # Adds links
    links = topo.getLinks()
    for linkname in links:
        topolink = links.get(linkname)
        srcnode = topolink.getSrcNode()
        dstnode = topolink.getDstNode()
        link = addlink(
            topology=toponame,
            linkname=linkname,
            srcnodename=srcnode.getResourceName(),
            srcportname=topolink.getSrcPort().getResourceName(),
            dstnodename=dstnode.getResourceName(),
            dstportname=topolink.getDstPort().getResourceName())
        link.getProperties().putAll(topolink.getProperties())
        newtopo.saveResource(link)
        newtopo.properties[Links][linkname] = newtopo.getResourceAnchor(link)
    newtopo.save()

def createpops(popsname,inv):
    inventory = Container.getContainer(inv)
    pops = createtopo(popsname)
    pops.properties[Pops] = {}
    for (popname,hwname,coreroutername,swname,links) in testbedPops.values():
        pop = Resource(popname)
        hwswitch = addnode(popsname,hwname)
        swswitch = addnode(popsname,swname)
        corerouter = addnode(popsname,coreroutername)
        hwswitch.setParentResourceAnchor(inventory.getResourceAnchor(hwname))
        swswitch.setParentResourceAnchor(inventory.getResourceAnchor(swname))
        corerouter.setParentResourceAnchor(inventory.getResourceAnchor(coreroutername))
        pops.saveResource(hwswitch)
        pops.saveResource(swswitch)
        pops.saveResource(corerouter)
        pop.properties[HwSwitch] = pops.getResourceAnchor(hwswitch)
        pop.properties[SwSwitch] = pops.getResourceAnchor(swswitch)
        pop.properties[CoreRouter] = pops.getResourceAnchor(corerouter)
        pop.properties[Links] = {}
        # Find and add the POP testbed host
        for tbn in tbns.values():
            if tbn['pop'] == popname:
                host = addnode(popsname,tbn['name'])
                host.setParentResourceAnchor(inventory.getResourceAnchor(tbn['name']))
                pops.saveResource(host)
        for (srcnodename,srcportname,dstnodename,dstportname) in links:
            linkname = Link.buildName(srcnodename,srcportname,dstnodename,dstportname)
            invlink = inventory.loadResource(linkname)
            if invlink == None:
                print "Cannot find link in inventory: ",linkname
                return
            link = addlink(topology=popsname,
                           linkname=linkname,
                           srcnodename=srcnodename,
                           srcportname=srcportname,
                           dstnodename=dstnodename,
                           dstportname=dstportname)
            if link == None:
                print "Could not add link " + linkname
            pop.properties[Links][linkname] = pops.getResourceAnchor(linkname)
            link.setParentResourceAnchor(inventory.getResourceAnchor(invlink))
            pops.saveResource(link)
            # Reverse link
            linkname = Link.buildName(dstnodename,dstportname,srcnodename,srcportname)
            invlink = inventory.loadResource(linkname)
            if invlink == None:
                print "Cannot find reverse link in inventory: ",linkname
                continue
            pop.properties[Links][linkname] = inventory.getResourceAnchor(linkname)
        pops.saveResource(pop)
        pops.properties[Pops][popname] = pops.getResourceAnchor(pop)
    pops.save()
    return pops

def createlink (srcpop,dstpop,vlanbase,maxiter):
    srcnode = Container.fromAnchor(srcpop.properties[CoreRouter])
    dstnode = Container.fromAnchor(dstpop.properties[CoreRouter])
    srcports = srcnode.properties[Ports]
    srcpop.properties['counter'] += 1
    dstpop.properties['counter'] += 1
    srcportindex = srcpop.properties['counter'] % len(srcports)
    dstports = dstnode.properties[Ports]
    dstportindex = dstpop.properties['counter'] % len(dstports)
    vlan = vlanbase
    while maxiter > 0:
        if reduce(lambda x,y: x and y,
                  map (lambda x :not vlan in x,
                       [srcpop.properties['vlanmap'],dstpop.properties['vlanmap']])):
            # VLAN is available in both ports
            srcport = srcports.keys()[srcportindex]
            dstport = dstports.keys()[dstportindex]
            srcpop.properties['vlanmap'].append(vlan)
            dstpop.properties['vlanmap'].append(vlan)
            return (srcport,dstport,vlan)
        vlan += 1
        maxiter -= 1
    return None



def createcorelinks(containername,popsname,vlanbase,maxiter=10):
    pops = Container.getContainer(popsname)
    links = createtopo(containername)
    popsmap={}
    for [src,dst] in poptopology:
        if (not src in popsmap):
            pop = pops.loadResource(src)
            if pop == None:
                print "cannot find " + src + " in " + containername
                return None
            pop.properties['counter'] = 0
            pop.properties['vlanmap'] = []
            popsmap[src] = pop
        if (not dst in popsmap):
            pop = pops.loadResource(dst)
            if pop == None:
                print "cannot find " + src + " in " + containername
                return None
            pop.properties['counter'] = 0
            popsmap[dst] = pop
            pop.properties['vlanmap'] = []
        srcpop = popsmap.get(src)
        dstpop = popsmap.get(dst)
        (srcportname,dstportname,vlan) = createlink(srcpop,dstpop,vlanbase,maxiter)
        # Create a new Port resources for this vlan
        srcrouter = srcpop.properties[CoreRouter]
        dstrouter = dstpop.properties[CoreRouter]
        link = (srcrouter['resourceName'],srcportname,dstrouter['resourceName'],dstportname,vlanbase)
        print link


def print_syntax():
    print "ESnet Testbed Utility"
    print "tbctl <cmd> <cmds options>"
    print " Commands are:"
    print "\thelp"
    print "\t\tPrints this help."
    print "\tcreate-inv <container name>"
    print "\t\tCreate a new container with the testbed network elements. Many of tbctl commands"
    print "\t\t\trequire an inventory container."
    print "\tcreate-pops <container name> inv <container name>"
    print "\tcreate-corelinks <container name> pops <container name> vlan <base vlan> [max <max. vlan iteration>"
    print "\t\tcreates the links between POP's."

if __name__ == '__main__':
    argv = sys.argv

    if len(argv) == 1:
        print_syntax()
        sys.exit()
    cmd = argv[1]
    if cmd == "help":
        print_syntax()
    elif cmd == "create-inv":
        topology = argv[2]
        createinv (topology)
    elif cmd == "create-pops":
        pops = argv[2]
        inventory = argv[4]
        createpops(pops,inventory)
    elif cmd == "create-corelinks":
        topology = argv[2]
        pops = argv[4]
        vlanbase = int(argv[6])
        maxiter = 10
        if len(argv) > 7:
            maxiter = int(argv[8])
        createcorelinks(topology,pops,vlanbase,maxiter)
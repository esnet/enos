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

from layer2.testbed.topoctl import createtopo,addnode,addlink,getnode
from layer2.testbed.topology import TestbedTopology
from layer2.testbed.builder import tbns,epipelinks,getPopRouter,testbedPops

from net.es.netshell.api import Container,Link,Resource

HwSwitch = "HwSwitch"
SwSwitch = "SwSwitch"
CoreRouter = "CoreRouter"
Links = "Links"

def createinv(toponame):
    newtopo = createtopo(toponame)
    topo = TestbedTopology()
    # Adds nodes
    nodes = topo.getNodes()
    for nodename in nodes:
        toponode = nodes.get(nodename)
        # Add this node to the topology
        node = addnode(toponame,nodename)
        node.getProperties().putAll(toponode.getProperties())

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

def createpops(popsname,inv):
    inventory = Container.getContainer(inv)
    pops = createtopo(popsname)
    pops.properties['pops'] = {}
    for (popname,hwname,corerouter,swname,links) in testbedPops.values():
        pop = Resource(popname)
        pop.properties[HwSwitch] = inventory.getResourceAnchor(hwname)
        pop.properties[SwSwitch] = inventory.getResourceAnchor(swname)
        pop.properties[CoreRouter] = inventory.getResourceAnchor(corerouter)
        pop.properties[Links] = {}
        for (srcnodename,srcportname,dstnodename,dstportname) in links:
            linkname = Link.buildName(srcnodename,srcportname,dstnodename,dstportname)
            invlink = inventory.loadResource(linkname)
            if invlink == None:
                print "Cannot find link in inventory: ",linkname
                continue
            pop.properties[Links][linkname] = inventory.getResourceAnchor(linkname)
            # Reverse link
            linkname = Link.buildName(dstnodename,dstportname,srcnodename,srcportname)
            invlink = inventory.loadResource(linkname)
            if invlink == None:
                print "Cannot find reverse link in inventory: ",linkname
                continue
            pop.properties[Links][linkname] = inventory.getResourceAnchor(linkname)
        pops.saveResource(pop)
        return pops



def createEpipeLink(srcnode,dstnode):
    link = Link(srcnode.getResourceName() + "-" + dstnode.getResourceName())
    link.setWeight(1)
    if not 'counter' in srcnode.properties:
        srcnode.properties['counter'] = 0
    srccount = srcnode.properties['counter']
    return link

def epipetopo(toponame,inv):
    inventory = Container.getContainer(inv)
    newtopo = createtopo(toponame)
    nodes = {}
    for [src,dst] in epipelinks:
        srcnode = None
        dstnode = None
        if not src in nodes:
            srcnode = addnode(toponame,src)
            router = getnode(inv,getPopRouter(src))
            anchor = inventory.getResourceAnchor(router)
            srcnode.setParentResourceAnchor(anchor)
            nodes[src] = [srcnode,router]
            newtopo.saveResource(srcnode)
        else:
            srcnode = nodes[src]

        if not dst in nodes:
            dstnode = addnode(toponame,dst)
            router = getnode(inv,getPopRouter(dst))
            anchor = inventory.getResourceAnchor(router)
            dstnode.setParentResourceAnchor(anchor)
            nodes[dst] = [dstnode,router]
            newtopo.saveResource(dstnode)
        else:
            dstnode = nodes[dst]

        addlink(toponame,src + "-" + dst,src,dst)
        addlink(toponame,dst + "-" + src,dst,src)

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
    print "\tepipe-topo <container name> inv <container name>"
    print "\t\tcreates the epipe topology into a new topology container."

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
    elif cmd == "epipe-topo":
        topology = argv[2]
        inventory = argv[4]
        epipetopo(topology,inventory)
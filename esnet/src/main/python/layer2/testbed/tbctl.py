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
from layer2.testbed.builder import tbns,epipelinks,getPopRouter

from net.es.netshell.api import Container,ResourceAnchor


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

def epipetopo(toponame,inv):
    inventory = Container.getContainer(inv)
    newtopo = createtopo(toponame)
    topo = TestbedTopology()
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


def print_syntax():
    print "ESnet Testbed Utility"
    print "tbctl <cmd> <cmds options>"
    print " Commands are:"
    print "\thelp"
    print "\t\tPrints this help."
    print "\tcreate-inv <inventory name>"
    print "\t\tCreate a new container with the testbed network elements"
    print "\tepipe-topo <topology name> inv <inventory name>"
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
    elif cmd == "epipe-topo":
        topology = argv[2]
        inventory = argv[4]
        epipetopo(topology,inventory)

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

from layer2.testbed.topoctl import createtopo,addnode,addlink
from layer2.testbed.topology import TestbedTopology
from layer2.testbed.builder import tbns


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



def print_syntax():
    print "ESnet Testbed Utility"
    print "tbctl <cmd> <cmds options>"
    print " Commands are:"
    print "\thelp"
    print "\t\tPrints this help."
    print "\tcreate-inv <inventory name>"
    print "\t\tCreate a new container with the testbed network elements"

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

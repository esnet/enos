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


from net.es.netshell.api import Container,Node,Port,Link,Resource

PortKey="Port"
PortsKey="Ports"
LinkKey="Links"
LinksKey="Links"
NodeKey="Node"
NodesKey="Nodes"
HostKey="Host"
HostsKey="Host"
SrcPortKey="SrcPort"
DstPortKey="DstPort"
VlanKey="VLAN"

def toPortResourceName(node,port,vlan):
    return node + "--" + port + "--" + str(vlan)

def toPortName(port):
    return port.split("--")[1]

def toPortVlan(port):
    return port.split("--")[2]

def createtopo(topology):
    Container.createContainer(topology)
    container = Container.getContainer(topology)
    return container

def deletetopo(topology):
    container = Container.getContainer(topology)
    if container != None:
        container.deleteContainer()

def addnode(topology,nodename):
    container = Container.getContainer(topology)
    if container == None:
        print topology,"does not exist."
        return None
    node = Node(nodename)
    node.properties[PortsKey] = {}
    container.saveResource(node)
    return node

def getnode(topology,nodename):
    container = Container.getContainer(topology)
    if container == None:
        print topology,"does not exist."
        return None
    return container.loadResource(nodename)

def delnode(topology,nodename):
    container = Container.getContainer(topology)
    if container == None:
        print topology,"does not exist."
        return False
    node = container.loadResource(nodename)
    if node == None:
        print nodename,"does not exist"
        return False
    node.delete(container)
    return True

def addlink(topology,linkname,srcnodename,dstnodename,srcportname,dstportname,srcvlan=0,dstvlan=0):

    container = None
    if isinstance(topology,Container):
        container = topology
    else:
        container = Container.getContainer(topology)
    if container == None:
        print "topology ",topology," does not exist."
        return None
    srcnode = container.loadResource(srcnodename)
    if srcnode == None:
        print "src node ",srcnodename," does not exist"
        return None
    dstnode = container.loadResource(dstnodename)
    if dstnode == None:
        print "dst node ",dstnodename," does not exist"
        return None
    link = Link(linkname)
    srcport =  container.loadResource(toPortResourceName(srcnodename,srcportname,srcvlan));
    if srcport == None:
        srcport = Port(toPortResourceName(srcnodename,srcportname,srcvlan))
        srcnode.properties[PortsKey][srcportname] = {}
        srcport.properties[LinksKey] = {}
        srcport.properties[VlanKey] = srcvlan
        srcport.properties[NodeKey] = container.getResourceAnchor(srcnode)
        container.saveResource(srcport)
    srcnode.properties[PortsKey][srcportname] = container.getResourceAnchor(srcport)
    srcport.properties[LinksKey][linkname] = container.getResourceAnchor(link)
    dstport =  container.loadResource(toPortResourceName(dstnodename,dstportname,dstvlan));
    if dstport == None:
        dstport = Port(toPortResourceName(dstnodename,dstportname,dstvlan))
        dstnode.properties[PortsKey][dstportname]= {}
        dstport.properties[LinksKey] = {}
        dstport.properties[NodeKey] = container.getResourceAnchor(dstnode)
        dstport.properties[VlanKey] = dstvlan
        container.saveResource(dstport)
    dstnode.properties[PortsKey][dstportname] = container.getResourceAnchor(dstport)
    dstport.properties[LinksKey][linkname] = container.getResourceAnchor(link)
    link.properties[SrcPortKey] = container.getResourceAnchor(srcport)
    link.properties[DstPortKey] = container.getResourceAnchor(dstport)
    link.setWeight(1) # default
    container.saveResource(link)
    container.saveResource(srcport)
    container.saveResource(dstport)
    container.saveResource(srcnode)
    container.saveResource(dstnode)
    return link

def dellink(topology,linkname,srcnodename,dstnodename,both=False):
    container = Container.getContainer(topology)
    if container == None:
        print topology,"does not exist."
        return False
    print "not yet implemented"
    return False

def print_syntax():
    print
    print "topoctl <cmd> <cmds options>"
    print "topoctl <toplogy> <cmd> <cmds options>"
    print "Manipulates generic topologies."
    print " Commands are:"
    print "\thelp"
    print "\t\tPrints this help."
    print "\tcreate <topology name>"
    print "\t\tcreates a new topology."
    print "\tdelete <topology name>"
    print "\t\tdeletes a new topology."
    print "\t<topology> add-node <node name>:"
    print "\t\t adds a node in the topology."
    print "\t<toploogy> del-node <node name>:"
    print "\t\t deletes a node in the topology."
    print "\t<toploogy> add-link <link name> <src> <dst> :"
    print"\t\tCreates a link between two nodes of the topology."
    print"\t\tthe opposite links is automatically added."
    print "\t<toploogy> del-link <link name> <src> <dst>:"
    print"\t\tDeletes a link between two nodes of the topology."
    print"\t\tthe opposite links is automatically deleted."

if __name__ == '__main__':
    argv = sys.argv

    if len(argv) == 1:
        print_syntax()
        sys.exit()
    cmd = argv[1]
    if cmd == "help":
        print_syntax()
    elif cmd == "reload":
        print "reloading topoctl"
        from layer2.testbed import topoctl
        reload(topoctl)
    elif cmd == "create":
        topology = argv[2]
        createtopo (topology)
    elif cmd == "delete":
        topology = argv[2]
        deletetopo (topology)
    else:
        topology = argv[1]
        cmd = argv[2]
        if cmd  == "add-node":
            nodename = argv[3]
            addnode(topology,nodename)
        elif cmd == "del-node":
            nodename = argv[3]
            delnode(topology,nodename)
        elif cmd == "add-link":
            linkname = argv[3]
            srcnodename = argv[4]
            dstnodename = argv[5]
            both = False
            if len(argv) > 6:
                if argv[6] == "both":
                    both = True
            addlink(topology,linkname,srcnodename,dstnodename,both)






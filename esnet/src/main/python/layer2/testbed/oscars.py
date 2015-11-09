#
# ENOS, Copyright (c) 2015, The Regents of the University of California,
# through Lawrence Berkeley National Laboratory (subject to receipt of any
# required approvals from the U.S. Dept. of Energy).  All rights reserved.
#
# If you have questions about your rights to use or distribute this software,
# please contact Berkeley Lab's Technology Transfer Department at TTD@lbl.gov.
#
# NOTICE.  This software is owned by the U.S. Department of Energy.  As such,
# the U.S. Government has been granted for itself and others acting on its
# behalf a paid-up, nonexclusive, irrevocable, worldwide license in the Software
# to reproduce, prepare derivative works, and perform publicly and display
# publicly.  Beginning five (5) years after the date permission to assert
# copyright is obtained from the U.S. Department of Energy, and subject to
# any subsequent five (5) year renewals, the U.S. Government is granted for
# itself and others acting on its behalf a paid-up, nonexclusive, irrevocable,
# worldwide license in the Software to reproduce, prepare derivative works,
# distribute copies to the public, perform publicly and display publicly, and
# to permit others to do so.
#

from net.es.netshell.api import TopologyFactory,TopologyProvider
from net.es.enos.esnet import OSCARSReservations
from org.joda.time import DateTime



topology = TopologyFactory.instance()
topo = topology.retrieveTopologyProvider("localLayer2")

def makeURN (node,domain="es.net",port="",link=""):
    """
    makeURN takes the name and domain of a node and builds a URN following the NMWG
    topology format that is used by IDCP that OSCARS implements. The format is as follow:
            urn:ogf:network:domain:node:port:link

    for instance: urn:ogf:network:domain=es.net:node=denv-cr5:port=9/1/4:link=*

    :param node: node name, i.e. star-cr5
    :param domain: domain name. Default is es.net
    :param port
    :param link
    :return: string
    """
    return  "urn:ogf:network:domain=" \
            + domain + ":node=" + node + ":port=" + port + ":link=" + link;

def parseURN (urn):
    """
    Parse a URN and returns the name and domain of the node.
    :param urn:  string
    :return:  a tuple (node,domain,port,link)
    """

    (x,y,z,domain,node,port,link) = tuple(urn.split(":"))
    if domain and "domain=" in domain:
        (x,domain) = domain.split('=')
    if node and "node=" in node:
        (x,node) = node.split('=')
    if port and "port=" in port:
        (x,port) = port.split('=')
    if link and "link=" in link:
        (x,link) = link.split('=')
    return(node,domain,port,link)

def getgrinode(gri,node,domain="es.net"):
    segments = gri.getSegments()
    for segment in segments:
        ports = segment.getPorts()
        (srcDom,srcNode,srcPort,srcVlan) = decodeURN(ports[0])
        if (srcNode,srcDom) == (node,domain):
            return (srcNode,srcDom,srcPort,srcVlan)
        (dstDom,dstNode,dstPort,dstVlan) = decodeURN(ports[1])
        if (dstNode,dstDom) == (node,domain):
            return (dstNode,dstDom,dstPort,dstVlan)
    return None

def getgri(name):
    start = DateTime.now()
    end = start.plusHours(2)
    gris={}
    reservations = OSCARSReservations(topo).retrieveScheduledCircuits()
    for res in reservations:
        if name == res.getName():
            return res
    return None

def getgris(match=None):
    gris={}
    reservations = OSCARSReservations(topo).retrieveScheduledCircuits()
    for res in reservations:
        gri = res.getName()
        desc = res.getDescription()
        if match != None:
            if match in desc:
                gris[gri] =res
        else:
            gris[gri] = res
    return gris

def decodeURN(urn):
    tmp = urn.split(":")
    domain = tmp[3]
    node = tmp[4]
    port = tmp[5].split(".")[0]
    vlan = ""
    if "." in tmp[5]:
        vlan = tmp[5].split(".")[1]
    return  (domain,node,port,vlan)

def displaygri(gri,name=None):
    if name == None:
        name = gri.getName()
    print "GRI",name,"\t",gri.getDescription()
    print "\tstart",gri.getStartDateTime(),"ends",gri.getEndDateTime()
    print "\t\tPath:"
    segments = gri.getSegments()
    for segment in segments:
        ports = segment.getPorts()
        (srcDom,srcNode,srcPort,srcVlan) = decodeURN(ports[0])
        (dstDom,dstNode,dstPort,dstVlan) = decodeURN(ports[1])
        print "\t\t",srcNode + "@" + srcDom,"port",srcPort,"vlan",srcVlan,"---",dstNode + "@" + dstDom,"port",dstPort,"vlan",dstVlan




def print_syntax():
    print
    print "oscars <cmd> <cmds options>"
    print "OSCARS control CLI"
    print " Commands are:"
    print "\nhelp"
    print "\tPrints this help."
    print "\nshow-gri <host name | all> [grep <string>] Displays information about a reservation or all reservations"
    print


if __name__ == '__main__':


    argv = sys.argv

    cmd = argv[1]
    if cmd == "help":
        print_syntax()
    elif cmd == "show-gri":
        gri = argv[2]
        if gri == 'all':
            match = None
            if 'grep' in argv:
                match = argv[4]
            for (name,gri) in getgris(match=match).items():
                displaygri(name,gri)
                print
        else:
            gri = getgri(argv[2])
            if (gri == None):
                print "unknown",argv[2]
                sys.exit()
            displaygri(gri)


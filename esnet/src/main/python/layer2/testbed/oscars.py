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
from net.es.netshell.api import TopologyFactory,TopologyProvider
from net.es.enos.esnet import OSCARSReservations
from org.joda.time import DateTime



topology = TopologyFactory.instance()
esnet = topology.retrieveTopologyProvider("localLayer2")

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
    reservations = OSCARSReservations(esnet).retrieveScheduledCircuits()
    for res in reservations:
        if name == res.getName():
            return res
    return None

def getgris(match=None,active=True):

    gris={}
    start = DateTime.now()
    end = start.plusHours(2)

    reservations = OSCARSReservations(esnet).retrieveScheduledCircuits()
    for res in reservations:
        if active and (not res.isActive(start,end)):
            continue
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

def griendpoints(gri):
    endpoint1 = None
    endpoint2 = None
    globals()['gri'] = gri
    segments = gri.getSegments()
    for segment in segments:
        ports = segment.getPorts()
        (srcDom,srcNode,srcPort,srcVlan) = decodeURN(ports[0])
        if endpoint1 == None:
            endpoint1 = (srcDom,srcNode,srcPort,srcVlan)
        # Only the last tuple of the iteration is the endpoint. We are interested, as destination, to the port
        # on the core router, which is the last source.
        endpoint2 =  (srcDom,srcNode,srcPort,srcVlan)
    return (endpoint1,endpoint2)

def displaygri(gri,name=None):
    if name == None:
        name = gri.getName()
    (e1,e2) = griendpoints(gri)
    print "GRI",name,"\t",gri.getDescription()
    print "\tfrom",e1[1],e1[0],e1[2],e1[3],"dest",e2[1],e2[0],e2[2],e2[3]
    print "\tstart",gri.getStartDateTime(),"ends",gri.getEndDateTime()
    print "\t\tPath:"
    segments = gri.getSegments()
    for segment in segments:
        ports = segment.getPorts()
        (srcDom,srcNode,srcPort,srcVlan) = decodeURN(ports[0])
        (dstDom,dstNode,dstPort,dstVlan) = decodeURN(ports[1])
        print "\t\t",srcNode + "@" + srcDom,"port",srcPort,"vlan",srcVlan,"\t---",dstNode + "@" + dstDom,"port",dstPort,"vlan",dstVlan


def getcoregris(pop1=None,pop2=None):
    """
    Returns the list of reservations that are
    :param pop1:
    :param pop2:
    :return:
    """
    reservations = getgris("ENOS:CORE:")
    gris = {}
    for (x,res) in reservations.items():
        desc = res.getDescription()
        if pop1 != None:
            if not pop1 in desc:
                continue
        if pop2 != None:
            if not pop2 in desc:
                continue
        gris[res.getName()] = res
    return gris

def print_syntax():
    print
    print "oscars <cmd> <cmds options>"
    print "OSCARS control CLI"
    print " Commands are:"
    print "\thelp"
    print "\tPrints this help."
    print "\tshow-gri <gri | all> [grep <string>] Displays a reservation by it gri or all reservations"
    print "\t\tAn optional string to match can be provided."
    print "\tshow-core [<pop1>] [<pop2>]  [grep <string>] display reservations between two testbed POPs,"
    print "\t\tor between all hosts. An optional string to match can be provided."



if __name__ == '__main__':


    argv = sys.argv

    if len(argv) == 1:
        print_syntax()
        sys.exit()
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
                displaygri(gri=gri,name=name)
                print
        else:
            gri = getgri(argv[2])
            if (gri == None):
                print "unknown",argv[2]
                sys.exit()
            displaygri(gri)
    elif cmd == "show-core":
        pop1 = None
        pop2 = None
        match = None
        if not"grep" in argv:
            if len(argv) > 2:
                pop1 = argv[2]
            if len(argv) > 3:
                pop2 = argv[3]
        else:
            if len(argv) == 5:
                pop1 = argv[2]
                match = argv[4]
            if len(argv) == 6:
                pop2 = argv[5]
        for (name,gri) in getcoregris(pop1=pop1,pop2=pop2).items():
            displaygri(gri=gri,name=name)
            print


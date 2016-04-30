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

def vcendpoints(vc):
    """
    Given a Link object representing a virtual circuit, return the parsed endpoints.
    This is roughly analogus to griendpoints for OSCARS.
    :param vc: Link (Resource) object
    :return: array of array of (domain, node name, port name, vlan)
    """
    srcportanchor = vc.properties['SrcPort']
    dstportanchor = vc.properties['DstPort']

    srcport = Container.fromAnchor(srcportanchor)
    dstport = Container.fromAnchor(dstportanchor)

    srcnode = Container.fromAnchor(srcport.properties['Node'])
    dstnode = Container.fromAnchor(dstport.properties['Node'])

    srcendpoint = (str(srcnode.properties['Domain']),
                   str(srcport.properties['Node']['resourceName']),
                   str(srcport.resourceName.split("--")[1]),
                   str(srcport.properties['VLAN']))
    dstendpoint = (str(dstnode.properties['Domain']),
                   str(dstport.properties['Node']['resourceName']),
                   str(dstport.resourceName.split("--")[1]),
                   str(dstport.properties['VLAN']))
    return (srcendpoint, dstendpoint)

def getvcnode(vc, node, domain= "es.net"):
    """
    Given a Link object and a node, figure out which endpoint corresponds to the node
    and return the nodename, domain, port, and VLAN
    :param vc: Link to test
    :param node: Name of the node of interest
    :param domain: Domain
    :return: array of (node name, domain, port name, vlan)
    """
    endpoints = vcendpoints(vc)
    if (endpoints[0][1], endpoints[0][0]) == (node, domain):
        return(endpoints[0][1], endpoints[0][0], endpoints[0][2], endpoints[0][3])
    if (endpoints[1][1], endpoints[1][0]) == (node, domain):
        return(endpoints[1][1], endpoints[1][0], endpoints[1][2], endpoints[1][3])
    return None


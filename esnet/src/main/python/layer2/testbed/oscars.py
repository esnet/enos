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



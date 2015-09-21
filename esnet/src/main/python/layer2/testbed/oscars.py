

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



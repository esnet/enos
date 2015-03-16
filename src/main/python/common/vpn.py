from net.es.netshell.api import GenericGraph,GenericHost, GenericLink,GenericPort

__author__ = 'lomax'

class VPN:
    """VPN provides the generic API to any VPN implementation.
    A VPN consist of a graph of sites (GenericNode) connected by links (GenericLinks) in any form of topology.
    The topology itself is logical: the links are logical links and do not represent the real path.
    """

    def __init__(self, graph):
        """
        :param graph: net.es.netshell.api.GenericGraph. Graph representing the logical VPN topology                                                                                           Crdate
        :return:
        """
        self.graph = graph

    def setUp(self):
        """ set up (activate) the VPN

        :return:
        """



    def tearDown(self):
         """  tear down (shutdown) the VPN

         :return:
         """











if __name__ == '__main__':
    h1 = GenericHost("site 1")
    h2 = GenericHost("site 2")
    p1 = GenericPort("eth0")
    p2 = GenericPort("eth0")
    link = GenericLink(h1,p1,h2,p2)

    graph = GenericGraph()
    graph.addVertex(h1)
    graph.addVertex(h2)
    graph.addEdge(h1,h2,link)



    vpn = VPN(graph=graph)










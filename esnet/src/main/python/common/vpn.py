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
from net.es.netshell.api import GenericGraph,GenericHost, GenericLink,GenericPort

__author__ = 'lomax'
from intent.py import ProvisioningIntent

class VPN:
    """VPN provides the generic API to any VPN implementation.
    A VPN consist of a graph of sites (GenericNode) connected by links (GenericLinks) in any form of topology.
    The topology itself is logical: the links are logical links and do not represent the real path.
    """

    def __init__(self, intent):
        """
        :param intent: intended VPN (ProvisioningIntent)
        :return:
        """
        self.intent = intent

    def setUp(self):
        """ set up (activate) the VPN

        :return:
        """
        print "not implemented"



    def tearDown(self):
        """  tear down (shutdown) the VPN

        :return:
        """
        print "not implemented"


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










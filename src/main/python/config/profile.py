#
# Generic profile that imports typical ENOS API
#

from net.es.netshell.api import NetworkFactory

layer2 = NetworkFactory.instance().retrieveNetworkProvider("localLayer2")
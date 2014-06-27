#
# Generic profile that imports typical ENOS API
#

from net.es.enos.api import NetworkFactory

layer2 = NetworkFactory.instance().retrieveNetworkProvider("localLayer2")
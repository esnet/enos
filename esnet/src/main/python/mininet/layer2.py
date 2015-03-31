from common.intent import ProvisioningRenderer, ProvisioningIntent
from common.api import Site
from mininet.enos import TestbedTopology
from net.es.netshell.api import GenericGraph, GenericHost


class Layer2(object):

    _instance = None


    def __new__(cls, *args, **kwargs):
        """
        Implements a singleton
        """
        if not cls._instance:
            cls._instance = super(Layer2, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        """
        Generic constructor.
        """

    def setupLink(self,node,port,link):
        """

        :param node: GenericNode
        :param port: GenericPort
        :param link: GenericLink
        :return:
        """
        remoteNode = None
        if link.getSrcNode().getResourceName() == node.getResourceName():
            remoteNode = link.getDstNode()
        else:
            remoteNode = link.getSrcNode()
        if issubclass(remoteNode.__class__,GenericHost):
            # Remote node is a host. All traffic coming from this port/vlan must be forwarded to the
            # border router



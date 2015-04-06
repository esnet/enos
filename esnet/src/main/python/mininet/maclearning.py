from common.intent import ProvisioningRenderer, ProvisioningIntent
from common.api import Site,Properties
from common.openflow import ScopeOwner,L2SwitchScope

from mininet.enos import TestbedTopology

from net.es.netshell.api import GenericGraph, GenericHost


class MACLearning(Properties):
    _instance = None

    def __new__(cls, *args, **kwargs):
        """
        Implements a singleton
        """
        if not cls._instance:
            cls._instance = super(MACLearning, cls).__new__(cls, *args, **kwargs)
        return cls._instance


    def __init__(self,hosts,wanRouter):
        """
        :return:
        """

